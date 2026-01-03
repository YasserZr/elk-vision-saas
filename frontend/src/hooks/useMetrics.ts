/**
 * React hook for real-time metrics WebSocket connection.
 * Streams live metrics (logs/sec, errors/min, connected users) from the backend.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService, Notification } from '@/lib/websocket';

export interface RealtimeMetrics {
  logs_per_second: number;
  errors_per_minute: number;
  warnings_per_minute: number;
  criticals_per_minute: number;
  connected_users: number;
  top_sources: Array<{ source: string; count: number }>;
  level_distribution: Record<string, number>;
}

export interface MetricsHistory {
  logs_per_second: Array<[number, number]>; // [timestamp, value]
  errors_per_minute: Array<[number, number]>;
}

interface UseMetricsReturn {
  isConnected: boolean;
  metrics: RealtimeMetrics | null;
  history: MetricsHistory | null;
  refresh: () => void;
}

/**
 * Hook for managing metrics WebSocket connection.
 * Automatically connects and handles reconnection.
 */
export function useMetrics(): UseMetricsReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<RealtimeMetrics | null>(null);
  const [history, setHistory] = useState<MetricsHistory | null>(null);
  const wsRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    // Create WebSocket service for metrics
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    let wsHost: string;
    if (process.env.NEXT_PUBLIC_WS_URL) {
      wsHost = process.env.NEXT_PUBLIC_WS_URL;
    } else if (process.env.NEXT_PUBLIC_API_URL) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL
        .replace('/api', '')
        .replace('/ws', '')
        .replace('http://', '')
        .replace('https://', '');
      wsHost = `${wsProtocol}//${apiUrl}`;
    } else {
      wsHost = `${wsProtocol}//localhost:8000`;
    }
    
    const wsUrl = `${wsHost}/ws/metrics/`;

    wsRef.current = new WebSocketService({
      url: wsUrl,
      onMessage: (notification: Notification) => {
        if (notification.type === 'metrics_update' && notification.data) {
          setMetrics(notification.data as RealtimeMetrics);
        } else if (notification.type === 'metrics_history' && notification.data) {
          setHistory(notification.data as MetricsHistory);
        }
      },
      onConnect: () => {
        setIsConnected(true);
        console.log('Metrics WebSocket connected');
      },
      onDisconnect: () => {
        setIsConnected(false);
        console.log('Metrics WebSocket disconnected');
      },
      onError: (error) => {
        console.error('Metrics WebSocket error:', error);
      },
    });

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  const refresh = useCallback(() => {
    wsRef.current?.send({ type: 'refresh' });
  }, []);

  return {
    isConnected,
    metrics,
    history,
    refresh,
  };
}
