# Real-Time Notifications with WebSockets

This implementation provides real-time notifications for alerts and log events using Django Channels (WebSockets) on the backend and a WebSocket service on the frontend.

## Architecture Overview

```
┌─────────────┐         WebSocket          ┌──────────────┐
│   Frontend  │ ◄─────────────────────────► │   Backend    │
│  (Next.js)  │    /ws/notifications/       │   (Django)   │
│             │    /ws/logs/stream/         │   Channels   │
└─────────────┘                             └──────────────┘
                                                    │
                                                    │
                                            ┌───────▼────────┐
                                            │  Redis Channel │
                                            │     Layer      │
                                            └────────────────┘
```

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install channels==4.0.0 channels-redis==4.1.0 daphne==4.0.0
```

### 2. Update Django Settings

The following has been added to `backend/config/settings.py`:

```python
INSTALLED_APPS = [
    "daphne",  # Must be first
    # ... other apps
    "channels",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(config("REDIS_HOST", default="redis"), 6379)],
        },
    },
}
```

### 3. WebSocket Consumers

Two consumers are available:

#### NotificationConsumer (`/ws/notifications/`)
Handles general notifications:
- Alert notifications
- System notifications
- Upload status updates
- Log event notifications

#### LogStreamConsumer (`/ws/logs/stream/`)
Streams real-time log entries with filtering support.

### 4. Sending Notifications

Use the utility functions in `backend/api/websocket_utils.py`:

```python
from api.websocket_utils import send_alert_notification, send_log_stream

# Send alert to specific user
send_alert_notification(user_id=1, alert_data={
    'id': 'alert-123',
    'severity': 'high',
    'title': 'High CPU Usage',
    'message': 'CPU usage exceeded 90%',
    'source': 'monitoring',
})

# Stream new log entry
send_log_stream({
    'id': 'log-456',
    'timestamp': '2025-12-29T10:30:00Z',
    'level': 'error',
    'message': 'Database connection failed',
    'source': 'api-server',
    'environment': 'production',
})
```

### 5. Automatic Notifications

Signals automatically send notifications when new alerts or logs are created:

```python
# In your log processing code
from api.signals import notify_log_ingested

notify_log_ingested({
    'timestamp': datetime.utcnow().isoformat(),
    'level': 'error',
    'message': 'Application crashed',
    'source': 'app-server',
})
```

## Frontend Integration

### 1. Using the NotificationCenter Component

Add to your dashboard layout or header:

```tsx
import { NotificationCenter } from '@/components/notifications';

export default function DashboardLayout() {
  return (
    <div>
      <Header>
        <NotificationCenter position="top-right" />
      </Header>
      {/* ... */}
    </div>
  );
}
```

Props:
- `position`: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
- `maxToasts`: Maximum number of toast notifications (default: 3)
- `autoHideDuration`: Auto-hide duration in ms (default: 5000)

### 2. Using WebSocket Hooks

#### useNotifications Hook

```tsx
import { useNotifications } from '@/hooks/useWebSocket';

function MyComponent() {
  const { isConnected, notifications, clearNotifications, subscribe } = useNotifications(
    (notification) => {
      // Handle each notification
      console.log('New notification:', notification);
      
      if (notification.type === 'alert' && notification.data?.severity === 'critical') {
        // Show critical alert
        alert(notification.data.message);
      }
    }
  );

  return (
    <div>
      <p>Connection: {isConnected ? 'Connected' : 'Disconnected'}</p>
      <p>Total notifications: {notifications.length}</p>
      <button onClick={clearNotifications}>Clear</button>
    </div>
  );
}
```

#### useLogStream Hook

```tsx
import { useLogStream } from '@/hooks/useWebSocket';

function LogViewer() {
  const { isConnected, logs, clearLogs, setFilters } = useLogStream((log) => {
    console.log('New log:', log);
  });

  // Apply filters
  const handleFilterChange = () => {
    setFilters({
      level: 'error',
      source: 'api-server',
      environment: 'production',
    });
  };

  return (
    <div>
      <h2>Real-time Logs ({logs.length})</h2>
      <button onClick={handleFilterChange}>Show Errors Only</button>
      <button onClick={clearLogs}>Clear</button>
      
      {logs.map((log, i) => (
        <div key={i}>
          [{log.level}] {log.message}
        </div>
      ))}
    </div>
  );
}
```

### 3. Using the LogStream Component

Complete real-time log viewer with filters:

```tsx
import LogStream from '@/components/dashboard/LogStream';

export default function LogsPage() {
  return (
    <div className="h-screen">
      <LogStream maxLogs={100} showFilters={true} />
    </div>
  );
}
```

### 4. Direct WebSocket Service Usage

For advanced use cases:

```tsx
import { WebSocketService } from '@/lib/websocket';

// Create custom WebSocket connection
const ws = new WebSocketService({
  url: 'ws://localhost:8000/ws/custom/',
  onMessage: (notification) => {
    console.log('Received:', notification);
  },
  onConnect: () => console.log('Connected'),
  onDisconnect: () => console.log('Disconnected'),
  reconnectDelay: 3000,
  maxReconnectAttempts: 10,
});

ws.connect();

// Send message
ws.send({ type: 'subscribe', topics: ['alerts', 'logs'] });

// Disconnect
ws.disconnect();
```

## Notification Types

### Alert Notification
```json
{
  "type": "alert",
  "data": {
    "id": "alert-123",
    "severity": "high|medium|low|critical",
    "title": "Alert Title",
    "message": "Alert message",
    "source": "system|logs|monitoring",
    "metadata": {}
  },
  "timestamp": "2025-12-29T10:30:00Z"
}
```

### Log Event Notification
```json
{
  "type": "log_event",
  "data": {
    "id": "log-456",
    "level": "error",
    "message": "Log message",
    "source": "api-server",
    "environment": "production"
  },
  "timestamp": "2025-12-29T10:30:00Z"
}
```

### System Notification
```json
{
  "type": "system",
  "data": {
    "title": "System Update",
    "message": "Maintenance scheduled",
    "severity": "info"
  },
  "timestamp": "2025-12-29T10:30:00Z"
}
```

### Upload Status Notification
```json
{
  "type": "upload_status",
  "data": {
    "upload_id": "upload-789",
    "status": "completed|processing|failed",
    "progress": 100,
    "filename": "logs.csv",
    "message": "Upload completed successfully"
  },
  "timestamp": "2025-12-29T10:30:00Z"
}
```

## Running the Application

### Start Redis (required for Channel Layer)

```bash
docker run -d -p 6379:6379 redis:alpine
```

### Start Django with Daphne (ASGI server)

```bash
cd backend
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Or use the development server (supports both HTTP and WebSocket):

```bash
python manage.py runserver
```

### Start Frontend

```bash
cd frontend
npm run dev
```

## Environment Variables

Add to your `.env` files:

### Backend (.env)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Frontend (.env.local)
```bash
# WebSocket URL (defaults to current host if not set)
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Or for production with SSL
NEXT_PUBLIC_WS_URL=wss://your-domain.com
```

## Testing WebSocket Connections

### Using Browser DevTools

1. Open browser DevTools → Network tab
2. Filter by "WS" (WebSocket)
3. Connect to the application
4. You should see WebSocket connections to `/ws/notifications/` and `/ws/logs/stream/`
5. Click on a connection to see messages

### Using Python Test Script

```python
import asyncio
import websockets
import json

async def test_notifications():
    uri = "ws://localhost:8000/ws/notifications/"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        message = await websocket.recv()
        print(f"Connected: {message}")
        
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Receive pong
        response = await websocket.recv()
        print(f"Pong: {response}")
        
        # Listen for notifications
        while True:
            message = await websocket.recv()
            print(f"Notification: {message}")

asyncio.run(test_notifications())
```

## Troubleshooting

### WebSocket Connection Fails

1. Check Redis is running: `redis-cli ping` should return `PONG`
2. Verify ASGI application is running (not WSGI)
3. Check browser console for connection errors
4. Ensure CORS settings allow WebSocket connections

### Notifications Not Appearing

1. Check WebSocket connection status (green dot in NotificationCenter)
2. Verify backend is sending notifications (check logs)
3. Test with browser DevTools to see raw WebSocket messages
4. Check Channel Layer configuration in Django settings

### Reconnection Issues

The WebSocket service automatically reconnects with exponential backoff:
- Initial delay: 3 seconds
- Max attempts: 10
- Delay increases with each attempt (max 5x)

## Production Considerations

1. **Use SSL**: Configure `wss://` protocol for production
2. **Load Balancing**: Use sticky sessions or Redis pub/sub
3. **Authentication**: Token-based auth is implemented via URL parameter
4. **Rate Limiting**: Implement rate limiting for WebSocket connections
5. **Monitoring**: Monitor WebSocket connection counts and message rates
6. **Scaling**: Use Redis Cluster for horizontal scaling

## Example Integration

See the updated components:
- `frontend/src/components/notifications/NotificationCenter.tsx` - Main notification component
- `frontend/src/components/dashboard/Header.tsx` - Integration example
- `frontend/src/components/dashboard/LogStream.tsx` - Real-time log viewer
- `frontend/src/hooks/useWebSocket.ts` - React hooks for WebSocket
- `backend/api/consumers.py` - WebSocket consumers
- `backend/api/websocket_utils.py` - Helper functions
