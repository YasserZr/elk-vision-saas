"""
Signal handlers for sending real-time WebSocket notifications.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
# from app.alerts.models import Alert  # TODO: Uncomment when Alert model is created
from api.websocket_utils import send_alert_notification, send_log_stream
import logging

logger = logging.getLogger(__name__)


# @receiver(post_save, sender=Alert)
def alert_created_handler(sender, instance, created, **kwargs):
    """
    Send WebSocket notification when a new alert is created.
    """
    if created:
        try:
            # Prepare alert data
            alert_data = {
                'id': str(instance.id),
                'severity': instance.severity,
                'title': instance.title,
                'message': instance.message,
                'source': getattr(instance, 'source', 'system'),
                'created_at': instance.created_at.isoformat() if hasattr(instance, 'created_at') else None,
                'metadata': getattr(instance, 'metadata', {}),
            }
            
            # Send notification to the user who should receive it
            # If alert has user_id, send to that user; otherwise broadcast
            user_id = getattr(instance, 'user_id', None)
            if user_id:
                send_alert_notification(user_id, alert_data)
            else:
                # Broadcast to all users or handle differently
                logger.info(f"New alert created: {alert_data['title']}")
        
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")


def notify_log_ingested(log_data):
    """
    Helper function to be called when a log is ingested.
    This should be called from the log processing code.
    
    Args:
        log_data: Dictionary containing log entry data
    """
    try:
        # Format log data for WebSocket transmission
        formatted_log = {
            'id': log_data.get('_id') or log_data.get('id'),
            'timestamp': log_data.get('timestamp'),
            'level': log_data.get('level', 'info'),
            'message': log_data.get('message', ''),
            'source': log_data.get('source'),
            'environment': log_data.get('environment'),
            'service_name': log_data.get('service_name'),
            'metadata': log_data.get('metadata', {}),
        }
        
        # Send to log stream
        send_log_stream(formatted_log)
        
        # If log is error/critical, also send as alert notification
        if log_data.get('level') in ['error', 'critical']:
            alert_data = {
                'id': formatted_log['id'],
                'severity': 'high' if log_data.get('level') == 'critical' else 'medium',
                'title': f"{log_data.get('level', '').upper()} Log Event",
                'message': log_data.get('message', '')[:200],
                'source': log_data.get('source', 'logs'),
                'metadata': {
                    'log_id': formatted_log['id'],
                    'level': log_data.get('level'),
                    'service': log_data.get('service_name'),
                }
            }
            # This would need user context to send to specific users
            logger.info(f"High severity log detected: {alert_data['title']}")
    
    except Exception as e:
        logger.error(f"Error sending log stream notification: {e}")
