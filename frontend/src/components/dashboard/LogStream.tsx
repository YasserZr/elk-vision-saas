/**
 * Real-time Log Stream Component
 * Displays live log entries as they arrive via WebSocket
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useLogStream } from '@/hooks/useWebSocket';
import { Card, Button, Spinner } from '@/components/ui';

interface LogStreamProps {
  maxLogs?: number;
  showFilters?: boolean;
}

export default function LogStream({ maxLogs = 500, showFilters = true }: LogStreamProps) {
  const [filters, setFilters] = useState({
    level: '',
    source: '',
    environment: '',
    searchText: '',
  });
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [pausedLogs, setPausedLogs] = useState<any[]>([]);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { isConnected, logs, clearLogs, setFilters: applyFilters } = useLogStream((log) => {
    // Handle each new log
    if (isPaused) {
      setPausedLogs((prev) => [log, ...prev].slice(0, maxLogs));
    }
    
    // You can add custom logic here, e.g., play sound for critical errors
    if (log.level === 'critical' || log.level === 'error') {
      console.warn('Critical log received:', log);
    }
  });

  const displayLogs = isPaused ? pausedLogs : logs;

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && !isPaused && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, isPaused]);

  // Handle spacebar to pause/resume
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault();
        setIsPaused((prev) => !prev);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  useEffect(() => {
    // Apply filters when they change
    const activeFilters = Object.entries(filters).reduce((acc, [key, value]) => {
      if (value) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);

    if (Object.keys(activeFilters).length > 0) {
      applyFilters(activeFilters);
    }
  }, [filters, applyFilters]);

  // Filter logs for text search (client-side)
  const filteredLogs = displayLogs.filter((log) => {
    if (filters.searchText) {
      const searchLower = filters.searchText.toLowerCase();
      const messageMatch = log.message?.toLowerCase().includes(searchLower);
      const levelMatch = log.level?.toLowerCase().includes(searchLower);
      const sourceMatch = log.source?.toLowerCase().includes(searchLower);
      if (!messageMatch && !levelMatch && !sourceMatch) return false;
    }
    return true;
  });

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      debug: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
      info: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
      error: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
      critical: 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200',
    };
    return colors[level] || colors.info;
  };

  const handleResume = () => {
    setIsPaused(false);
    // Clear paused logs buffer
    setPausedLogs([]);
  };

  return (
    <Card className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Real-time Log Stream
          </h3>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`}
            />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
          {isPaused && pausedLogs.length > 0 && (
            <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-xs font-medium rounded">
              Paused ({pausedLogs.length} new)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Auto-scroll toggle */}
          <Button
            variant={autoScroll ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setAutoScroll(!autoScroll)}
            title="Toggle auto-scroll"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            Auto-scroll
          </Button>

          {isPaused ? (
            <Button variant="primary" size="sm" onClick={handleResume}>
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
              Resume
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setIsPaused(true)}>
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Pause
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={clearLogs}>
            Clear
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex flex-wrap gap-3">
            <input
              type="text"
              placeholder="Search logs..."
              value={filters.searchText}
              onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
              className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 flex-1 min-w-[200px]"
            />

            <select
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>

            <input
              type="text"
              placeholder="Filter by source..."
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

            <input
              type="text"
              placeholder="Filter by environment..."
              value={filters.environment}
              onChange={(e) => setFilters({ ...filters, environment: e.target.value })}
              className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
            />

            {(filters.level || filters.source || filters.environment || filters.searchText) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ level: '', source: '', environment: '', searchText: '' })}
              >
                Clear Filters
              </Button>
            )}
          </div>
          
          {/* Keyboard shortcuts hint */}
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            <kbd className="px-2 py-0.5 bg-white dark:bg-gray-900 rounded border border-gray-300 dark:border-gray-600">Space</kbd> to pause/resume
          </div>
        </div>
      )}

      {/* Log Stream */}
      <div ref={logsContainerRef} className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-900 font-mono text-sm">
        {!isConnected && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Spinner size="lg" className="mb-3" />
              <p>Connecting to log stream...</p>
            </div>
          </div>
        )}

        {isConnected && filteredLogs.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>Waiting for log entries...</p>
              <p className="text-xs mt-1">Live logs will appear here</p>
            </div>
          </div>
        )}

        {filteredLogs.map((log, index) => (
          <div
            key={log.id || index}
            className="flex items-start gap-3 p-2 rounded bg-gray-800 hover:bg-gray-750 transition-colors border-l-2 border-transparent hover:border-blue-500"
          >
            {/* Timestamp */}
            <span className="text-gray-500 text-xs whitespace-nowrap flex-shrink-0 w-24">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>

            {/* Level Badge */}
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLevelColor(log.level)} flex-shrink-0`}>
              {log.level?.toUpperCase()}
            </span>

            {/* Source */}
            {log.source && (
              <span className="text-purple-400 text-xs flex-shrink-0">
                [{log.source}]
              </span>
            )}

            {/* Message */}
            <span className="text-gray-300 flex-1 break-words">
              {log.message}
            </span>

            {/* Environment */}
            {log.environment && (
              <span className="text-gray-500 text-xs flex-shrink-0">
                {log.environment}
              </span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{filteredLogs.length} logs displayed (max {maxLogs})</span>
          <span>{autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}</span>
        </div>
      </div>
    </Card>
  );
}
