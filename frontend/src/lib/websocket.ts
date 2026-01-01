/**
 * WebSocket service for real-time notifications and log streaming.
 * Handles connection, reconnection, and message processing.
 */

/**
 * Get access token from localStorage
 */
function getAccessToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

export type NotificationType = 'alert' | 'log_event' | 'system' | 'upload_status' | 'connection' | 'error' | 'new_log' | 'log_batch' | 'pong';

export interface Notification {
  type: NotificationType;
  data?: any;
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
  onMessage?: (notification: Notification) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingTimer: NodeJS.Timeout | null = null;
  private isIntentionalClose = false;
  private messageQueue: any[] = [];

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectDelay: 3000,
      maxReconnectAttempts: 10,
      pingInterval: 30000,
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.isIntentionalClose = false;

    try {
      // Get access token for authentication
      const token = getAccessToken();
      const wsUrl = token 
        ? `${this.config.url}?token=${token}`
        : this.config.url;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionalClose = true;
    this.clearTimers();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Send message to WebSocket server
   */
  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      // Queue message for sending when connection is established
      this.messageQueue.push(data);
    }
  }

  /**
   * Subscribe to specific notification types
   */
  subscribe(subscriptions: string[]): void {
    this.send({
      type: 'subscribe',
      subscriptions,
    });
  }

  /**
   * Check connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('WebSocket connected:', this.config.url);
    this.reconnectAttempts = 0;

    // Start ping interval for keepalive
    this.startPingInterval();

    // Send queued messages
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }

    // Call onConnect callback
    this.config.onConnect?.();
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const notification: Notification = JSON.parse(event.data);
      
      // Handle pong responses
      if (notification.type === 'pong') {
        return;
      }

      // Call onMessage callback
      this.config.onMessage?.(notification);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.config.onError?.(event);
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.clearTimers();

    // Call onDisconnect callback
    this.config.onDisconnect?.();

    // Attempt reconnection if not intentional
    if (!this.isIntentionalClose) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectDelay! * Math.min(this.reconnectAttempts, 5);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start ping interval for keepalive
   */
  private startPingInterval(): void {
    this.pingTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, this.config.pingInterval!);
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

/**
 * Create WebSocket service for notifications
 */
export function createNotificationService(onMessage: (notification: Notification) => void): WebSocketService {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // Get base WebSocket URL from environment or derive from API URL
  let wsHost: string;
  if (process.env.NEXT_PUBLIC_WS_URL) {
    wsHost = process.env.NEXT_PUBLIC_WS_URL;
  } else if (process.env.NEXT_PUBLIC_API_URL) {
    // Convert HTTP API URL to WebSocket URL
    // Handle both http://localhost:8000/api and http://localhost:8000 formats
    const apiUrl = process.env.NEXT_PUBLIC_API_URL
      .replace('/api', '')
      .replace('/ws', '')  // Remove /ws if present
      .replace('http://', '')
      .replace('https://', '');
    wsHost = `${wsProtocol}//${apiUrl}`;
  } else {
    // Default to backend port
    wsHost = `${wsProtocol}//localhost:8000`;
  }
  
  const wsUrl = `${wsHost}/ws/notifications/`;
  console.log('WebSocket URL:', wsUrl); // Debug log

  return new WebSocketService({
    url: wsUrl,
    onMessage,
    onConnect: () => console.log('Notification service connected'),
    onDisconnect: () => console.log('Notification service disconnected'),
    onError: (error) => console.error('Notification service error:', error),
  });
}

/**
 * Create WebSocket service for log streaming
 */
export function createLogStreamService(onMessage: (notification: Notification) => void): WebSocketService {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // Get base WebSocket URL from environment or derive from API URL
  let wsHost: string;
  if (process.env.NEXT_PUBLIC_WS_URL) {
    wsHost = process.env.NEXT_PUBLIC_WS_URL;
  } else if (process.env.NEXT_PUBLIC_API_URL) {
    // Convert HTTP API URL to WebSocket URL
    // Handle both http://localhost:8000/api and http://localhost:8000 formats
    const apiUrl = process.env.NEXT_PUBLIC_API_URL
      .replace('/api', '')
      .replace('/ws', '')  // Remove /ws if present
      .replace('http://', '')
      .replace('https://', '');
    wsHost = `${wsProtocol}//${apiUrl}`;
  } else {
    // Default to backend port
    wsHost = `${wsProtocol}//localhost:8000`;
  }
  
  const wsUrl = `${wsHost}/ws/logs/stream/`;

  return new WebSocketService({
    url: wsUrl,
    onMessage,
    onConnect: () => console.log('Log stream connected'),
    onDisconnect: () => console.log('Log stream disconnected'),
    onError: (error) => console.error('Log stream error:', error),
  });
}
