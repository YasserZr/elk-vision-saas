import socket
import json
import logging
import time
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class LogstashForwarder:
    """
    Forward logs to Logstash with connection management, retries, and monitoring
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        protocol: str = 'tcp',
        timeout: int = 5,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize Logstash forwarder
        
        Args:
            host: Logstash host (default from settings)
            port: Logstash port (default from settings)
            protocol: Connection protocol (tcp/udp)
            timeout: Socket timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.host = host or getattr(settings, 'LOGSTASH_HOST', 'logstash')
        self.port = port or getattr(settings, 'LOGSTASH_PORT', 5000)
        self.protocol = protocol.lower()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.socket = None
        self._stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_retries': 0,
            'last_error': None,
            'last_success': None
        }
        
        logger.info(
            f"Initialized LogstashForwarder: {self.protocol}://{self.host}:{self.port}"
        )
    
    def connect(self) -> bool:
        """
        Establish connection to Logstash
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.host, self.port))
                logger.info(f"Connected to Logstash via TCP: {self.host}:{self.port}")
            elif self.protocol == 'udp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                logger.info(f"UDP socket created for Logstash: {self.host}:{self.port}")
            else:
                raise ValueError(f"Unsupported protocol: {self.protocol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Logstash: {e}")
            self._stats['last_error'] = str(e)
            return False
    
    def disconnect(self):
        """Close connection to Logstash"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Disconnected from Logstash")
            except Exception as e:
                logger.warning(f"Error closing Logstash connection: {e}")
            finally:
                self.socket = None
    
    def send_log(self, log_entry: Dict[str, Any]) -> bool:
        """
        Send a single log entry to Logstash
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_logs([log_entry])
    
    def send_logs(self, log_entries: List[Dict[str, Any]]) -> bool:
        """
        Send multiple log entries to Logstash with retry logic
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            bool: True if all logs sent successfully
        """
        if not log_entries:
            logger.warning("No log entries to send")
            return True
        
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.max_retries:
            try:
                # Ensure connection
                if not self.socket:
                    if not self.connect():
                        raise ConnectionError("Failed to connect to Logstash")
                
                # Send logs
                success_count = 0
                for log_entry in log_entries:
                    if self._send_single_entry(log_entry):
                        success_count += 1
                    else:
                        logger.warning(f"Failed to send log entry: {log_entry.get('message', '')[:100]}")
                
                # Update statistics
                self._stats['total_sent'] += success_count
                self._stats['last_success'] = time.time()
                
                if success_count == len(log_entries):
                    logger.info(f"Successfully sent {success_count} log entries to Logstash")
                    return True
                else:
                    logger.warning(
                        f"Partially sent logs: {success_count}/{len(log_entries)} successful"
                    )
                    return False
                
            except (ConnectionError, socket.error, OSError) as e:
                last_exception = e
                retry_count += 1
                self._stats['total_retries'] += 1
                
                logger.warning(
                    f"Failed to send logs to Logstash (attempt {retry_count}/{self.max_retries + 1}): {e}"
                )
                
                # Close and reconnect on next attempt
                self.disconnect()
                
                if retry_count <= self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error sending logs to Logstash: {e}", exc_info=True)
                self._stats['last_error'] = str(e)
                self._stats['total_failed'] += len(log_entries)
                return False
        
        # All retries exhausted
        logger.error(
            f"Failed to send {len(log_entries)} logs after {self.max_retries + 1} attempts. "
            f"Last error: {last_exception}"
        )
        self._stats['total_failed'] += len(log_entries)
        self._stats['last_error'] = str(last_exception)
        return False
    
    def _send_single_entry(self, log_entry: Dict[str, Any]) -> bool:
        """
        Send a single log entry through the socket
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Convert to JSON and add newline for Logstash
            message = json.dumps(log_entry) + '\n'
            message_bytes = message.encode('utf-8')
            
            if self.protocol == 'tcp':
                self.socket.sendall(message_bytes)
            elif self.protocol == 'udp':
                self.socket.sendto(message_bytes, (self.host, self.port))
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending single entry: {e}")
            raise
    
    def send_batch(
        self,
        log_entries: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Send logs in batches
        
        Args:
            log_entries: List of log entries
            batch_size: Number of logs per batch
            
        Returns:
            dict: Statistics (sent, failed)
        """
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(log_entries), batch_size):
            batch = log_entries[i:i + batch_size]
            
            if self.send_logs(batch):
                total_sent += len(batch)
            else:
                total_failed += len(batch)
        
        return {
            'sent': total_sent,
            'failed': total_failed,
            'total': len(log_entries)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Logstash connection health
        
        Returns:
            dict: Health status
        """
        try:
            # Try to establish connection
            if not self.socket:
                if not self.connect():
                    return {
                        'status': 'unhealthy',
                        'connected': False,
                        'error': 'Failed to connect'
                    }
            
            # Send test message
            test_log = {
                '@timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'message': 'Health check',
                'level': 'INFO',
                'source': 'health_check'
            }
            
            if self._send_single_entry(test_log):
                return {
                    'status': 'healthy',
                    'connected': True,
                    'host': self.host,
                    'port': self.port,
                    'protocol': self.protocol
                }
            else:
                return {
                    'status': 'unhealthy',
                    'connected': False,
                    'error': 'Failed to send test message'
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
        finally:
            self.disconnect()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get forwarder statistics
        
        Returns:
            dict: Statistics
        """
        return {
            'total_sent': self._stats['total_sent'],
            'total_failed': self._stats['total_failed'],
            'total_retries': self._stats['total_retries'],
            'success_rate': (
                self._stats['total_sent'] / 
                (self._stats['total_sent'] + self._stats['total_failed'])
                if (self._stats['total_sent'] + self._stats['total_failed']) > 0 
                else 0
            ),
            'last_error': self._stats['last_error'],
            'last_success': time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(self._stats['last_success'])
            ) if self._stats['last_success'] else None
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_retries': 0,
            'last_error': None,
            'last_success': None
        }
        logger.info("Statistics reset")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Singleton instance for reuse
_logstash_forwarder = None


def get_logstash_forwarder() -> LogstashForwarder:
    """
    Get or create singleton LogstashForwarder instance
    
    Returns:
        LogstashForwarder: Forwarder instance
    """
    global _logstash_forwarder
    
    if _logstash_forwarder is None:
        _logstash_forwarder = LogstashForwarder(
            host=getattr(settings, 'LOGSTASH_HOST', 'logstash'),
            port=getattr(settings, 'LOGSTASH_PORT', 5000),
            protocol=getattr(settings, 'LOGSTASH_PROTOCOL', 'tcp'),
            timeout=getattr(settings, 'LOGSTASH_TIMEOUT', 5),
            max_retries=getattr(settings, 'LOGSTASH_MAX_RETRIES', 3),
            retry_delay=getattr(settings, 'LOGSTASH_RETRY_DELAY', 2)
        )
    
    return _logstash_forwarder
