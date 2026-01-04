'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useLogStream } from '@/hooks/useWebSocket';
import LiveMetricsBar from '@/components/realtime/LiveMetricsBar';

const MAX_LOGS = 500;

export default function LiveLogsPage() {
  const [filters, setFilters] = useState({
    level: '',
    source: '',
    searchText: '',
  });
  const [autoScroll, setAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const [displayLogs, setDisplayLogs] = useState<any[]>([]);
  const logsBufferRef = useRef<any[]>([]);

  // Use log stream hook
  const { isConnected, logs } = useLogStream();

  // Update buffer when new logs arrive
  useEffect(() => {
    if (!isPaused && logs.length > 0) {
      logsBufferRef.current = [...logs.slice(-MAX_LOGS)];
      setDisplayLogs(logsBufferRef.current);
    }
  }, [logs, isPaused]);

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && logsContainerRef.current && !isPaused) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [displayLogs, autoScroll, isPaused]);

  // Filter logs
  const filteredLogs = displayLogs.filter((log) => {
    if (filters.level && log.level !== filters.level) return false;
    if (filters.source && log.source !== filters.source) return false;
    if (filters.searchText) {
      const searchLower = filters.searchText.toLowerCase();
      return (
        log.message?.toLowerCase().includes(searchLower) ||
        log.source?.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  const getLevelColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return 'text-red-400';
      case 'WARNING':
        return 'text-yellow-400';
      case 'INFO':
        return 'text-blue-400';
      case 'DEBUG':
        return 'text-gray-400';
      default:
        return 'text-gray-300';
    }
  };

  const getLevelBg = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-red-500/10 border-red-500/20';
      case 'WARNING':
        return 'bg-yellow-500/10 border-yellow-500/20';
      case 'INFO':
        return 'bg-blue-500/10 border-blue-500/20';
      case 'DEBUG':
        return 'bg-gray-500/10 border-gray-500/20';
      default:
        return 'bg-gray-500/10 border-gray-500/20';
    }
  };

  const clearLogs = () => {
    logsBufferRef.current = [];
    setDisplayLogs([]);
  };

  const togglePause = () => {
    setIsPaused(!isPaused);
    if (isPaused) {
      // Resume - update display with current buffer
      setDisplayLogs([...logsBufferRef.current]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Live Log Stream
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Real-time log monitoring with filtering and search
          </p>
        </div>

        {/* Live Metrics Bar */}
        <LiveMetricsBar />

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-4">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`}
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Filters */}
            <div className="flex-1 flex flex-wrap gap-3">
              <select
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Levels</option>
                <option value="DEBUG">Debug</option>
                <option value="INFO">Info</option>
                <option value="WARNING">Warning</option>
                <option value="ERROR">Error</option>
                <option value="CRITICAL">Critical</option>
              </select>

              <input
                type="text"
                placeholder="Search logs..."
                value={filters.searchText}
                onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
                className="flex-1 min-w-[200px] px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={togglePause}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isPaused
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                }`}
              >
                {isPaused ? (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                    </svg>
                    Resume
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Pause
                  </span>
                )}
              </button>

              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  autoScroll
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-600 hover:bg-gray-700 text-white'
                }`}
              >
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>

              <button
                onClick={clearLogs}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex gap-6 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Total Logs:</span>
              <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                {displayLogs.length}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Filtered:</span>
              <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                {filteredLogs.length}
              </span>
            </div>
            {isPaused && (
              <div className="text-yellow-600 dark:text-yellow-400 font-medium">
                ⏸ Stream Paused
              </div>
            )}
          </div>
        </div>

        {/* Logs Display */}
        <div className="bg-gray-900 rounded-lg shadow-lg border border-gray-700 overflow-hidden">
          <div
            ref={logsContainerRef}
            className="h-[600px] overflow-y-auto p-4 font-mono text-sm space-y-1"
          >
            {filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                {isConnected ? 'Waiting for logs...' : 'Disconnected from log stream'}
              </div>
            ) : (
              filteredLogs.map((log, index) => (
                <div
                  key={`${log.timestamp}-${index}`}
                  className={`p-3 rounded border ${getLevelBg(log.level)} hover:bg-opacity-20 transition-colors`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-gray-500 text-xs flex-shrink-0">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span
                      className={`${getLevelColor(log.level)} font-semibold text-xs uppercase flex-shrink-0 w-16`}
                    >
                      {log.level}
                    </span>
                    {log.source && (
                      <span className="text-blue-400 text-xs flex-shrink-0">
                        [{log.source}]
                      </span>
                    )}
                    <span className="text-gray-300 flex-1 break-all">
                      {log.message}
                    </span>
                  </div>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <div className="mt-2 pl-24 text-xs text-gray-500">
                      {JSON.stringify(log.metadata, null, 2)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
