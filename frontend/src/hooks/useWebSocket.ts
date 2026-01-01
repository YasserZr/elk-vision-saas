/**
 * React hooks for WebSocket functionality.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService, Notification, createNotificationService, createLogStreamService } from '@/lib/websocket';

/**
 * Hook for managing notification WebSocket connection
 */
export function useNotifications(onNotification?: (notification: Notification) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const wsRef = useRef<WebSocketService | null>(null);
  const callbackRef = useRef(onNotification);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = onNotification;
  }, [onNotification]);

  useEffect(() => {
    // Create WebSocket service
    wsRef.current = createNotificationService((notification) => {
      // Add to notifications array
      setNotifications((prev) => [notification, ...prev].slice(0, 50)); // Keep last 50

      // Call external callback using ref
      callbackRef.current?.(notification);
    });

    // Set up connection status tracking
    const originalOnConnect = wsRef.current['config'].onConnect;
    const originalOnDisconnect = wsRef.current['config'].onDisconnect;

    wsRef.current['config'].onConnect = () => {
      setIsConnected(true);
      originalOnConnect?.();
    };

    wsRef.current['config'].onDisconnect = () => {
      setIsConnected(false);
      originalOnDisconnect?.();
    };

    // Connect
    wsRef.current.connect();

    // Cleanup on unmount
    return () => {
      wsRef.current?.disconnect();
    };
  }, []); // Empty dependency array - only run once on mount

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const subscribe = useCallback((subscriptions: string[]) => {
    wsRef.current?.subscribe(subscriptions);
  }, []);

  return {
    isConnected,
    notifications,
    clearNotifications,
    subscribe,
  };
}

/**
 * Hook for managing log stream WebSocket connection
 */
export function useLogStream(onLog?: (log: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const wsRef = useRef<WebSocketService | null>(null);
  const callbackRef = useRef(onLog);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = onLog;
  }, [onLog]);

  useEffect(() => {
    // Create WebSocket service
    wsRef.current = createLogStreamService((notification) => {
      if (notification.type === 'new_log' && notification.data) {
        // Add to logs array
        setLogs((prev) => [notification.data, ...prev].slice(0, 100)); // Keep last 100

        // Call external callback using ref
        callbackRef.current?.(notification.data);
      } else if (notification.type === 'log_batch' && notification.data) {
        // Handle batch logs
        setLogs((prev) => [...notification.data, ...prev].slice(0, 100));
      }
    });

    // Set up connection status tracking
    const originalOnConnect = wsRef.current['config'].onConnect;
    const originalOnDisconnect = wsRef.current['config'].onDisconnect;

    wsRef.current['config'].onConnect = () => {
      setIsConnected(true);
      originalOnConnect?.();
    };

    wsRef.current['config'].onDisconnect = () => {
      setIsConnected(false);
      originalOnDisconnect?.();
    };

    // Connect
    wsRef.current.connect();

    // Cleanup on unmount
    return () => {
      wsRef.current?.disconnect();
    };
  }, []); // Empty dependency array - only run once on mount

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const setFilters = useCallback((filters: Record<string, any>) => {
    wsRef.current?.send({
      type: 'set_filters',
      filters,
    });
  }, []);

  return {
    isConnected,
    logs,
    clearLogs,
    setFilters,
  };
}
