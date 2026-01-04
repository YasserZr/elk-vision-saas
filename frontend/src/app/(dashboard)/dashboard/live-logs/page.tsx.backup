/**
 * Live Logs Page
 * 
 * Dedicated full-page experience for real-time log monitoring.
 * Similar to running 'tail -f' on log files with advanced filtering.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useLogStream } from '@/hooks/useWebSocket';
import LiveMetricsBar from '@/components/realtime/LiveMetricsBar';

const MAX_LOGS = 500; // Circular buffer size

export default function LiveLogsPage() {
  const [filters, setFilters] = useState({
    level: '',
    source: '',
    searchText: '',
  });
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [pausedLogs, setPausedLogs] = useState<any[]>([]);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { isConnected, logs } = useLogStream((log) => {
    if (isPaused) {
      setPausedLogs((prev) => [log, ...prev].slice(0, MAX_LOGS));
    }
  });

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

  const displayLogs = isPaused ? pausedLogs : logs;

  // Filter logs based on current filters
  const filteredLogs = displayLogs.filter((log) => {
    if (filters.level && log.level !== filters.level) return false;
    if (filters.source && !log.source?.toLowerCase().includes(filters.source.toLowerCase())) return false;
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
      debug: 'text-gray-500 dark:text-gray-400',
      info: 'text-blue-600 dark:text-blue-400',
      warning: 'text-yellow-600 dark:text-yellow-400',
      error: 'text-red-600 dark:text-red-400',
      critical: 'text-red-700 dark:text-red-300 font-bold',
    };
    return colors[level?.toLowerCase()] || colors.info;
  };

  const getLevelBadge = (level: string) => {
    const colors: Record<string, string> = {
      debug: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
      info: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
      error: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
      critical: 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200',
    };
    return colors[level?.toLowerCase()] || colors.info;
  };

  const handleResume = () => {
    setIsPaused(false);
    setPausedLogs([]);
  };

  const clearFilters = () => {
    setFilters({ level: '', source: '', searchText: '' });
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        fractionalSecondDigits: 3 
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Metrics Bar */}
      <LiveMetricsBar />

      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Live Logs
            </h1>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                }`}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
            {isPaused && pausedLogs.length > 0 && (
              <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-sm font-medium rounded-full">
                Paused · {pausedLogs.length} new logs
              </span>
            )}
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {filteredLogs.length} logs displayed
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Auto-scroll toggle */}
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                autoScroll
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
              }`}
            >
              <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
              Auto-scroll
            </button>

            {/* Pause/Resume */}
            {isPaused ? (
              <button
                onClick={handleResume}
                className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
                Resume
              </button>
            ) : (
              <button
                onClick={() => setIsPaused(true)}
                className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Pause
              </button>
            )}
          </div>
        </div>

        {/* Filters Row */}
        <div className="mt-4 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search logs..."
            value={filters.searchText}
            onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
            className="px-4 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm flex-1 min-w-[300px]"
          />

          <select
            value={filters.level}
            onChange={(e) => setFilters({ ...filters, level: e.target.value })}
            className="px-4 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
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
            className="px-4 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
          />

          {(filters.level || filters.source || filters.searchText) && (
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
          <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">Space</kbd> to pause/resume
        </div>
      </div>

      {/* Logs Container */}
      <div
        ref={logsContainerRef}
        className="flex-1 overflow-auto bg-gray-900 font-mono text-sm"
      >
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-lg">
                {isConnected ? 'Waiting for logs...' : 'Connecting...'}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={`${log.timestamp}-${index}`}
                className="flex gap-3 hover:bg-gray-800/50 px-2 py-1 rounded transition-colors"
              >
                {/* Timestamp */}
                <span className="text-gray-500 shrink-0 w-28">
                  {formatTimestamp(log.timestamp || log['@timestamp'])}
                </span>

                {/* Level Badge */}
                <span className={`shrink-0 w-20 text-center px-2 py-0.5 rounded text-xs font-medium ${getLevelBadge(log.level)}`}>
                  {log.level?.toUpperCase() || 'INFO'}
                </span>

                {/* Source */}
                {log.source && (
                  <span className="text-purple-400 shrink-0 max-w-xs truncate">
                    [{log.source}]
                  </span>
                )}

                {/* Message */}
                <span className={`flex-1 ${getLevelColor(log.level)}`}>
                  {log.message}
                </span>

                {/* File name if available */}
                {log.file_name && (
                  <span className="text-gray-600 dark:text-gray-500 shrink-0 text-xs">
                    {log.file_name}
                  </span>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
