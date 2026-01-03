"""
API module for real-time log streaming and WebSocket communication.

This module provides:
- WebSocket consumers for logs, notifications, and metrics
- Real-time bridge for Logstash → Redis → WebSocket
- Management commands for starting the real-time listener
"""

default_app_config = 'api.apps.ApiConfig'
