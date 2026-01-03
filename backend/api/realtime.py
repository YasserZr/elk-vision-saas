"""
Real-time log streaming infrastructure.

This module provides:
1. RedisPubSubBridge - Listens to Redis Pub/Sub for logs from Logstash
2. MetricsAggregator - Sliding window counters for real-time metrics
3. ConnectionTracker - Tracks active WebSocket connections

The Redis listener receives logs published by Logstash and broadcasts
them to connected WebSocket clients with <1 second latency.
"""

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


# =============================================================================
# Connection Tracker
# =============================================================================

class ConnectionTracker:
    """
    Thread-safe tracker for active WebSocket connections.
    Tracks connections per channel group.
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: Dict[str, Set[str]] = {}
            cls._instance._user_info: Dict[str, Dict[str, Any]] = {}
        return cls._instance
    
    async def add_connection(
        self, 
        group: str, 
        channel_name: str, 
        user_id: Optional[str] = None
    ) -> int:
        """Add a connection and return total count for the group."""
        async with self._lock:
            if group not in self._connections:
                self._connections[group] = set()
            self._connections[group].add(channel_name)
            
            if user_id:
                self._user_info[channel_name] = {
                    'user_id': user_id,
                    'connected_at': datetime.utcnow().isoformat(),
                    'group': group,
                }
            
            return len(self._connections[group])
    
    async def remove_connection(self, group: str, channel_name: str) -> int:
        """Remove a connection and return remaining count for the group."""
        async with self._lock:
            if group in self._connections:
                self._connections[group].discard(channel_name)
                if not self._connections[group]:
                    del self._connections[group]
            
            self._user_info.pop(channel_name, None)
            
            return len(self._connections.get(group, set()))
    
    def get_count(self, group: str) -> int:
        """Get current connection count for a group."""
        return len(self._connections.get(group, set()))
    
    def get_total_count(self) -> int:
        """Get total connections across all groups."""
        return sum(len(conns) for conns in self._connections.values())
    
    def get_all_counts(self) -> Dict[str, int]:
        """Get connection counts per group."""
        return {group: len(conns) for group, conns in self._connections.items()}


# Global instance
connection_tracker = ConnectionTracker()


# =============================================================================
# Metrics Aggregator
# =============================================================================

@dataclass
class SlidingWindowCounter:
    """Sliding window counter for time-based metrics."""
    window_seconds: int
    _events: deque = field(default_factory=deque)
    
    def add(self, timestamp: Optional[float] = None) -> None:
        """Add an event at the given timestamp (or now)."""
        ts = timestamp or time.time()
        self._events.append(ts)
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Remove events outside the window."""
        cutoff = time.time() - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()
    
    def count(self) -> int:
        """Get count of events in the window."""
        self._cleanup()
        return len(self._events)
    
    def rate_per_second(self) -> float:
        """Get events per second over the window."""
        self._cleanup()
        if not self._events:
            return 0.0
        return len(self._events) / self.window_seconds


class MetricsAggregator:
    """
    Aggregates real-time metrics with sliding windows.
    
    Tracks:
    - logs_per_second: 10-second sliding window
    - errors_per_minute: 60-second sliding window
    - warnings_per_minute: 60-second sliding window
    - level_distribution: 60-second window by level
    - source_distribution: 60-second window by source
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_counters()
        return cls._instance
    
    def _init_counters(self):
        """Initialize all counters."""
        self._logs_counter = SlidingWindowCounter(window_seconds=10)
        self._errors_counter = SlidingWindowCounter(window_seconds=60)
        self._warnings_counter = SlidingWindowCounter(window_seconds=60)
        self._criticals_counter = SlidingWindowCounter(window_seconds=60)
        
        # Per-level counters (60-second windows)
        self._level_counters: Dict[str, SlidingWindowCounter] = {}
        
        # Per-source counters (60-second windows)
        self._source_counters: Dict[str, SlidingWindowCounter] = {}
        
        # History for charts (last 5 minutes, sampled every second)
        self._logs_history: deque = deque(maxlen=300)
        self._errors_history: deque = deque(maxlen=300)
        self._last_sample_time = 0
    
    def record_log(self, log_data: Dict[str, Any]) -> None:
        """Record a log event for metrics."""
        now = time.time()
        
        # Total logs
        self._logs_counter.add(now)
        
        # By level
        level = log_data.get('level', 'info').lower()
        if level not in self._level_counters:
            self._level_counters[level] = SlidingWindowCounter(window_seconds=60)
        self._level_counters[level].add(now)
        
        # Track error/warning/critical separately
        if level == 'error':
            self._errors_counter.add(now)
        elif level == 'warning':
            self._warnings_counter.add(now)
        elif level == 'critical':
            self._criticals_counter.add(now)
            self._errors_counter.add(now)  # Also count as error
        
        # By source
        source = log_data.get('source') or log_data.get('service_name') or 'unknown'
        if source not in self._source_counters:
            self._source_counters[source] = SlidingWindowCounter(window_seconds=60)
        self._source_counters[source].add(now)
        
        # Sample for history (at most once per second)
        if now - self._last_sample_time >= 1.0:
            self._sample_history(now)
            self._last_sample_time = now
    
    def _sample_history(self, timestamp: float) -> None:
        """Sample current rates for history charts."""
        self._logs_history.append((timestamp, self._logs_counter.rate_per_second()))
        self._errors_history.append((timestamp, self._errors_counter.count()))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        # Build level distribution
        level_dist = {}
        for level, counter in self._level_counters.items():
            count = counter.count()
            if count > 0:
                level_dist[level] = count
        
        # Build top sources
        top_sources = []
        for source, counter in self._source_counters.items():
            count = counter.count()
            if count > 0:
                top_sources.append({'source': source, 'count': count})
        top_sources.sort(key=lambda x: x['count'], reverse=True)
        top_sources = top_sources[:10]  # Top 10
        
        return {
            'logs_per_second': round(self._logs_counter.rate_per_second(), 1),
            'errors_per_minute': self._errors_counter.count(),
            'warnings_per_minute': self._warnings_counter.count(),
            'criticals_per_minute': self._criticals_counter.count(),
            'connected_users': connection_tracker.get_count('log_stream'),
            'top_sources': top_sources,
            'level_distribution': level_dist,
        }
    
    def get_history(self) -> Dict[str, List]:
        """Get metrics history for charts."""
        return {
            'logs_per_second': list(self._logs_history),
            'errors_per_minute': list(self._errors_history),
        }


# Global instance
metrics_aggregator = MetricsAggregator()


# =============================================================================
# Redis Pub/Sub Bridge
# =============================================================================

class RedisPubSubBridge:
    """
    Listens to Redis Pub/Sub channel for logs from Logstash.
    Broadcasts received logs to WebSocket clients.
    """
    
    REDIS_CHANNEL = 'logs:realtime'
    
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._running = False
        self._channel_layer = None
        self._reconnect_delay = 1
        self._max_reconnect_delay = 30
    
    async def _get_redis_url(self) -> str:
        """Build Redis URL from settings."""
        host = getattr(settings, 'REDIS_HOST', 'redis')
        port = getattr(settings, 'REDIS_PORT', 6379)
        password = getattr(settings, 'REDIS_PASSWORD', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/0"
        return f"redis://{host}:{port}/0"
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            redis_url = await self._get_redis_url()
            self._redis = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=10.0,
                # No socket_timeout for pub/sub - we want to wait indefinitely for messages
            )
            
            # Test connection
            await self._redis.ping()
            
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(self.REDIS_CHANNEL)
            
            self._channel_layer = get_channel_layer()
            self._reconnect_delay = 1  # Reset delay on success
            
            logger.info(f"Connected to Redis, subscribed to '{self.REDIS_CHANNEL}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe(self.REDIS_CHANNEL)
                await self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None
        
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None
        
        logger.info("Disconnected from Redis")
    
    async def _process_message(self, message: Dict[str, Any]) -> None:
        """Process a received message from Redis."""
        if message['type'] != 'message':
            return
        
        try:
            # Parse log data
            raw_data = message['data']
            logger.debug(f"Received raw_data type={type(raw_data)}, value={raw_data!r}")
            
            if isinstance(raw_data, str):
                log_data = json.loads(raw_data)
            else:
                log_data = raw_data
            
            # Normalize the log data from Logstash format
            normalized_log = self._normalize_log(log_data)
            
            # Record metrics
            metrics_aggregator.record_log(normalized_log)
            
            # Broadcast to log stream WebSocket group
            if self._channel_layer:
                await self._channel_layer.group_send(
                    'log_stream',
                    {
                        'type': 'new_log',
                        'data': normalized_log,
                        'timestamp': datetime.utcnow().isoformat(),
                    }
                )
                
                # If error/critical, also send alert notification
                level = normalized_log.get('level', '').lower()
                if level in ('error', 'critical'):
                    await self._channel_layer.group_send(
                        'notifications_broadcast',
                        {
                            'type': 'alert_notification',
                            'data': {
                                'id': normalized_log.get('id'),
                                'severity': 'critical' if level == 'critical' else 'high',
                                'title': f"{level.upper()} Log Event",
                                'message': normalized_log.get('message', '')[:200],
                                'source': normalized_log.get('source', 'logs'),
                                'log_id': normalized_log.get('id'),
                            },
                            'timestamp': datetime.utcnow().isoformat(),
                        }
                    )
        
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in Redis message: {e}")
            logger.warning(f"Raw data repr: {raw_data!r}")
            logger.warning(f"Raw data type: {type(raw_data)}")
        except Exception as e:
            logger.error(f"Error processing Redis message: {e}")
    
    def _normalize_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize log data from Logstash format."""
        # Handle nested 'parsed' field from Logstash
        parsed = log_data.get('parsed', {})
        
        # Extract fields, preferring parsed over top-level
        return {
            'id': log_data.get('_id') or log_data.get('@metadata', {}).get('_id') or str(time.time()),
            'timestamp': log_data.get('@timestamp') or parsed.get('timestamp') or datetime.utcnow().isoformat(),
            'level': (parsed.get('level') or log_data.get('level', 'info')).lower(),
            'message': parsed.get('message') or log_data.get('message', ''),
            'source': parsed.get('source') or log_data.get('source') or log_data.get('host', {}).get('name'),
            'service_name': parsed.get('service_name') or log_data.get('service_name'),
            'environment': parsed.get('environment') or log_data.get('environment'),
            'metadata': {
                k: v for k, v in parsed.items()
                if k not in ('level', 'message', 'source', 'service_name', 'environment', 'timestamp')
            },
        }
    
    async def run(self) -> None:
        """Main loop: listen for messages and broadcast."""
        self._running = True
        
        while self._running:
            try:
                # Connect if not connected
                if not self._pubsub:
                    connected = await self.connect()
                    if not connected:
                        logger.warning(f"Reconnecting in {self._reconnect_delay}s...")
                        await asyncio.sleep(self._reconnect_delay)
                        self._reconnect_delay = min(
                            self._reconnect_delay * 2, 
                            self._max_reconnect_delay
                        )
                        continue
                
                # Listen for messages
                # Timeout is expected when no messages - this keeps the loop responsive
                async for message in self._pubsub.listen():
                    if not self._running:
                        break
                    await self._process_message(message)
                    
            except asyncio.CancelledError:
                logger.info("Redis listener cancelled")
                break
            except (TimeoutError, asyncio.TimeoutError):
                # Socket timeout is normal when no messages arrive
                # Continue listening without disconnecting
                continue
            except Exception as e:
                logger.error(f"Redis listener error: {e}")
                await self.disconnect()
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, 
                    self._max_reconnect_delay
                )
        
        await self.disconnect()
    
    def stop(self) -> None:
        """Signal the listener to stop."""
        self._running = False


# =============================================================================
# Metrics Broadcasting Task
# =============================================================================

async def broadcast_metrics_loop(interval_seconds: float = 1.0) -> None:
    """
    Periodically broadcast metrics to connected clients.
    Runs as a background task.
    """
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        logger.error("No channel layer configured, cannot broadcast metrics")
        return
    
    logger.info(f"Starting metrics broadcast loop (interval: {interval_seconds}s)")
    
    while True:
        try:
            metrics = metrics_aggregator.get_metrics()
            
            await channel_layer.group_send(
                'metrics_stream',
                {
                    'type': 'metrics_update',
                    'data': metrics,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
            
            await asyncio.sleep(interval_seconds)
            
        except asyncio.CancelledError:
            logger.info("Metrics broadcast loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error broadcasting metrics: {e}")
            await asyncio.sleep(interval_seconds)


# =============================================================================
# Synchronous Helpers (for use in Django views/signals)
# =============================================================================

def record_log_sync(log_data: Dict[str, Any]) -> None:
    """Synchronously record a log for metrics (for use in signals)."""
    metrics_aggregator.record_log(log_data)


def get_current_metrics() -> Dict[str, Any]:
    """Get current metrics snapshot (synchronous)."""
    return metrics_aggregator.get_metrics()


def get_metrics_history() -> Dict[str, List]:
    """Get metrics history for charts (synchronous)."""
    return metrics_aggregator.get_history()
