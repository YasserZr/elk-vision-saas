"""
WebSocket consumers for real-time notifications and log streaming.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications about alerts and system events.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        
        # Create user-specific notification channel
        self.notification_group = f"notifications_{self.user.id if self.user.is_authenticated else 'anonymous'}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'message': 'Connected to notification stream',
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group,
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
            
            # Handle subscription updates
            elif message_type == 'subscribe':
                subscriptions = data.get('subscriptions', [])
                # Store user subscriptions (can be saved to DB)
                await self.send(text_data=json.dumps({
                    'type': 'subscription_updated',
                    'subscriptions': subscriptions,
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': datetime.utcnow().isoformat()
            }))
    
    # Handler for alert notifications
    async def alert_notification(self, event):
        """Send alert notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event['data'],
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
    
    # Handler for log event notifications
    async def log_notification(self, event):
        """Send log event notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'log_event',
            'data': event['data'],
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
    
    # Handler for system notifications
    async def system_notification(self, event):
        """Send system notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'system',
            'data': event['data'],
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
    
    # Handler for upload status updates
    async def upload_notification(self, event):
        """Send upload status notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'upload_status',
            'data': event['data'],
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))


class LogStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time log streaming.
    Streams new log entries as they arrive.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.log_stream_group = "log_stream"
        
        # Join log stream group
        await self.channel_layer.group_add(
            self.log_stream_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'message': 'Connected to log stream',
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.log_stream_group,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle filters
            if message_type == 'set_filters':
                filters = data.get('filters', {})
                # Store filters for this connection
                self.filters = filters
                await self.send(text_data=json.dumps({
                    'type': 'filters_updated',
                    'filters': filters,
                    'timestamp': datetime.utcnow().isoformat()
                }))
            
            # Handle ping
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': datetime.utcnow().isoformat()
            }))
    
    # Handler for new log entries
    async def new_log(self, event):
        """Send new log entry to WebSocket."""
        log_data = event['data']
        
        # Apply filters if set
        if hasattr(self, 'filters') and self.filters:
            # Check level filter
            if 'level' in self.filters and log_data.get('level') != self.filters['level']:
                return
            
            # Check source filter
            if 'source' in self.filters and log_data.get('source') != self.filters['source']:
                return
            
            # Check environment filter
            if 'environment' in self.filters and log_data.get('environment') != self.filters['environment']:
                return
        
        await self.send(text_data=json.dumps({
            'type': 'new_log',
            'data': log_data,
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
    
    # Handler for batch log updates
    async def log_batch(self, event):
        """Send batch of log entries to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'log_batch',
            'data': event['data'],
            'count': len(event['data']),
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
        }))
