'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import { Spinner } from '@/components/ui';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  message: string;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface LogViewerProps {
  logs: LogEntry[];
  loading?: boolean;
  title?: string;
  maxHeight?: string;
  onLogClick?: (log: LogEntry) => void;
}

const levelColors = {
  debug: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  critical: 'bg-red-200 text-red-800 dark:bg-red-900/50 dark:text-red-300',
};

const levelIcons = {
  debug: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
    </svg>
  ),
  info: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  ),
  warning: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  error: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
  ),
  critical: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
};

export default function LogViewer({
  logs,
  loading = false,
  title = 'Recent Logs',
  maxHeight = '400px',
  onLogClick,
}: LogViewerProps) {
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  const filteredLogs = logs.filter((log) => {
    const matchesLevel = filter === 'all' || log.level === filter;
    const matchesSearch =
      searchQuery === '' ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.source?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle>{title}</CardTitle>
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              <input
                type="search"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-4 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 border border-transparent rounded-lg focus:outline-none focus:bg-white dark:focus:bg-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-40 sm:w-48"
              />
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            {/* Filter */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 border border-transparent rounded-lg focus:outline-none focus:bg-white dark:focus:bg-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              aria-label="Filter by level"
            >
              <option value="all">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className="space-y-2 overflow-y-auto pr-2 -mr-2"
          style={{ maxHeight }}
          role="log"
          aria-label="Log entries"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {logs.length === 0 ? 'No logs available' : 'No logs match your filter'}
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className={`
                  p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700
                  hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer
                `}
                onClick={() => {
                  setExpandedLog(expandedLog === log.id ? null : log.id);
                  onLogClick?.(log);
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setExpandedLog(expandedLog === log.id ? null : log.id);
                    onLogClick?.(log);
                  }
                }}
                aria-expanded={expandedLog === log.id}
              >
                <div className="flex items-start gap-3">
                  {/* Level badge */}
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${levelColors[log.level]}`}
                  >
                    {levelIcons[log.level]}
                    {log.level.toUpperCase()}
                  </span>
                  
                  {/* Main content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-words">
                      {log.message}
                    </p>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      {log.source && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Source: {log.source}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Expand indicator */}
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <svg
                      className={`w-4 h-4 text-gray-400 transition-transform ${expandedLog === log.id ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </div>
                
                {/* Expanded metadata */}
                {expandedLog === log.id && log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <pre className="text-xs text-gray-600 dark:text-gray-400 font-mono overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(log.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
