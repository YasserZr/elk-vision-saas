"""
WebSocket consumer for real-time metrics streaming.
Broadcasts live metrics (logs/sec, errors/min, connected users) every second.
"""

import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer

from api.realtime import metrics_aggregator, connection_tracker


class MetricsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time metrics.
    
    Clients receive metrics updates every ~1 second with:
    - logs_per_second
    - errors_per_minute
    - warnings_per_minute
    - connected_users
    - top_sources
    - level_distribution
    """
    
    METRICS_GROUP = 'metrics_stream'
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get("user")
        
        # Join metrics group
        await self.channel_layer.group_add(
            self.METRICS_GROUP,
            self.channel_name
        )
        
        # Track connection
        user_id = str(self.user.id) if self.user and self.user.is_authenticated else None
        count = await connection_tracker.add_connection(
            self.METRICS_GROUP, 
            self.channel_name,
            user_id
        )
        
        await self.accept()
        
        # Send connection confirmation with current metrics
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'message': 'Connected to metrics stream',
            'connected_clients': count,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Send initial metrics snapshot
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': metrics_aggregator.get_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Send metrics history for charts
        await self.send(text_data=json.dumps({
            'type': 'metrics_history',
            'data': metrics_aggregator.get_history(),
            'duration_minutes': 5,
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave metrics group
        await self.channel_layer.group_discard(
            self.METRICS_GROUP,
            self.channel_name
        )
        
        # Untrack connection
        await connection_tracker.remove_connection(
            self.METRICS_GROUP,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle ping/pong for keepalive
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }))
            
            # Handle manual refresh request
            elif message_type == 'refresh':
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'data': metrics_aggregator.get_metrics(),
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': datetime.utcnow().isoformat()
            }))
    
    # Handler for metrics broadcast
    async def metrics_update(self, event):
        """Send metrics update to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': event['data'],
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
