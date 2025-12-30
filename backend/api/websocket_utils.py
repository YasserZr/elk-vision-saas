"""
Utility functions for sending WebSocket notifications.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
import json


def send_notification(user_id, notification_type, data):
    """
    Send a notification to a specific user via WebSocket.
    
    Args:
        user_id: User ID to send notification to
        notification_type: Type of notification (alert, log_event, system, upload_status)
        data: Notification data dict
    """
    channel_layer = get_channel_layer()
    
    if channel_layer:
        notification_group = f"notifications_{user_id}"
        
        async_to_sync(channel_layer.group_send)(
            notification_group,
            {
                'type': f'{notification_type}_notification',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )


def broadcast_notification(notification_type, data):
    """
    Broadcast a notification to all connected users.
    
    Args:
        notification_type: Type of notification
        data: Notification data dict
    """
    channel_layer = get_channel_layer()
    
    if channel_layer:
        # This would need to iterate over all active user groups
        # For now, send to a general broadcast group
        async_to_sync(channel_layer.group_send)(
            "notifications_broadcast",
            {
                'type': f'{notification_type}_notification',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )


def send_log_stream(log_data):
    """
    Send a new log entry to the log stream.
    
    Args:
        log_data: Log entry data dict
    """
    channel_layer = get_channel_layer()
    
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            "log_stream",
            {
                'type': 'new_log',
                'data': log_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )


def send_alert_notification(user_id, alert_data):
    """
    Send an alert notification to a user.
    
    Args:
        user_id: User ID
        alert_data: Alert data including severity, title, message, etc.
    """
    send_notification(user_id, 'alert', {
        'id': alert_data.get('id'),
        'severity': alert_data.get('severity', 'info'),
        'title': alert_data.get('title', 'New Alert'),
        'message': alert_data.get('message', ''),
        'source': alert_data.get('source'),
        'metadata': alert_data.get('metadata', {}),
    })


def send_upload_status(user_id, upload_data):
    """
    Send upload status update to a user.
    
    Args:
        user_id: User ID
        upload_data: Upload status data
    """
    send_notification(user_id, 'upload', {
        'upload_id': upload_data.get('upload_id'),
        'status': upload_data.get('status'),
        'progress': upload_data.get('progress', 0),
        'filename': upload_data.get('filename'),
        'message': upload_data.get('message', ''),
        'result': upload_data.get('result'),
    })


def send_system_notification(user_id, title, message, severity='info'):
    """
    Send a system notification to a user.
    
    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        severity: Notification severity (info, warning, error, success)
    """
    send_notification(user_id, 'system', {
        'title': title,
        'message': message,
        'severity': severity,
    })
