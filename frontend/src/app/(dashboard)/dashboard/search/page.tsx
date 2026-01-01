'use client';

import { useState, useEffect, useCallback } from 'react';
import { logsApi } from '@/lib/api';
import { Button, Alert, Spinner, Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import DatePicker from '@/components/ui/DatePicker';
import SearchableTable, { Column } from '@/components/analytics/SearchableTable';

interface SearchFilters {
  query: string;
  level: string;
  service: string;
  source: string;
  environment: string;
  startDate: Date | null;
  endDate: Date | null;
}

interface LogEntry {
  _id: string;
  timestamp: string;
  '@timestamp': string;
  level: string;
  message: string;
  source: string;
  environment: string;
  service_name?: string;
  [key: string]: unknown;
}

interface SearchHistoryEntry {
  search_id: string;
  query: string;
  filters: Record<string, unknown>;
  results_count: number;
  created_at: string;
}

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
const ENVIRONMENTS = ['development', 'staging', 'production', 'testing'];

export default function SearchPage() {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    level: '',
    service: '',
    source: '',
    environment: '',
    startDate: null,
    endDate: null,
  });
  const [results, setResults] = useState<LogEntry[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  const PAGE_SIZE = 50;

  // Load search history on mount
  useEffect(() => {
    loadSearchHistory();
  }, []);

  const loadSearchHistory = async () => {
    try {
      const response = await logsApi.getSearchHistory(10);
      if (response && 'history' in response) {
        setSearchHistory((response as { history: SearchHistoryEntry[] }).history);
      }
    } catch (err) {
      console.error('Failed to load search history:', err);
    }
  };

  const handleSearch = useCallback(async (page: number = 1) => {
    setIsLoading(true);
    setError(null);
    setCurrentPage(page);

    try {
      const searchParams: Record<string, unknown> = {
        page,
        size: PAGE_SIZE,
      };

      if (filters.query) searchParams.q = filters.query;
      if (filters.level) searchParams.level = filters.level;
      if (filters.service) searchParams.service = filters.service;
      if (filters.source) searchParams.source = filters.source;
      if (filters.environment) searchParams.environment = filters.environment;
      if (filters.startDate) searchParams.from = filters.startDate.toISOString();
      if (filters.endDate) searchParams.to = filters.endDate.toISOString();

      const response = await logsApi.search(searchParams);

      if (response) {
        const data = response as unknown as { results: LogEntry[]; total: number };
        setResults(data.results || []);
        setTotalResults(data.total || 0);

        // Save to search history if has query or filters
        if (filters.query || filters.level || filters.service) {
          try {
            await logsApi.saveSearchHistory({
              query: filters.query,
              filters: {
                level: filters.level,
                service: filters.service,
                source: filters.source,
                environment: filters.environment,
                startDate: filters.startDate?.toISOString(),
                endDate: filters.endDate?.toISOString(),
              },
              results_count: data.total || 0,
            });
            loadSearchHistory();
          } catch {
            // Ignore history save errors
          }
        }
      }
    } catch (err) {
      setError('Failed to search logs. Please try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const handleReset = () => {
    setFilters({
      query: '',
      level: '',
      service: '',
      source: '',
      environment: '',
      startDate: null,
      endDate: null,
    });
    setResults([]);
    setTotalResults(0);
    setCurrentPage(1);
  };

  const applyHistoryEntry = (entry: SearchHistoryEntry) => {
    const historyFilters = entry.filters as Record<string, string>;
    setFilters({
      query: entry.query,
      level: historyFilters.level || '',
      service: historyFilters.service || '',
      source: historyFilters.source || '',
      environment: historyFilters.environment || '',
      startDate: historyFilters.startDate ? new Date(historyFilters.startDate) : null,
      endDate: historyFilters.endDate ? new Date(historyFilters.endDate) : null,
    });
    setShowHistory(false);
  };

  const deleteHistoryEntry = async (searchId: string) => {
    try {
      await logsApi.deleteSearchHistory(searchId);
      loadSearchHistory();
    } catch (err) {
      console.error('Failed to delete history entry:', err);
    }
  };

  const clearAllHistory = async () => {
    try {
      await logsApi.clearSearchHistory();
      setSearchHistory([]);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  const exportToCSV = () => {
    if (results.length === 0) return;

    const headers = ['Timestamp', 'Level', 'Service', 'Source', 'Environment', 'Message'];
    const rows = results.map((log) => [
      log['@timestamp'] || log.timestamp,
      log.level || '',
      log.service_name || '',
      log.source || '',
      log.environment || '',
      `"${(log.message || '').replace(/"/g, '""')}"`,
    ]);

    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-export-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const tableColumns: Column<LogEntry>[] = [
    {
      key: '@timestamp',
      header: 'Date/Time',
      width: '180px',
      sortable: true,
      render: (item) => (
        <span className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
          {new Date(item['@timestamp'] || item.timestamp).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'level',
      header: 'Level',
      width: '100px',
      sortable: true,
      filterable: true,
      render: (item) => {
        const levelColors: Record<string, string> = {
          debug: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
          info: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
          warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
          error: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
          critical: 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200',
        };
        const level = (item.level || 'info').toLowerCase();
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium ${levelColors[level] || levelColors.info}`}>
            {item.level?.toUpperCase() || 'INFO'}
          </span>
        );
      },
    },
    {
      key: 'service_name',
      header: 'Service',
      width: '140px',
      sortable: true,
      filterable: true,
      render: (item) => (
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {item.service_name || '-'}
        </span>
      ),
    },
    {
      key: 'message',
      header: 'Message',
      render: (item) => (
        <span className="text-sm text-gray-900 dark:text-gray-100 truncate block max-w-xl">
          {item.message}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '100px',
      render: (item) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            setSelectedLog(item);
          }}
        >
          View
        </Button>
      ),
    },
  ];

  const totalPages = Math.ceil(totalResults / PAGE_SIZE);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Search Logs</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Search and filter through your log entries
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowHistory(!showHistory)}
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            History
          </Button>
          {results.length > 0 && (
            <Button variant="outline" onClick={exportToCSV}>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export CSV
            </Button>
          )}
        </div>
      </div>

      {/* Search History Panel */}
      {showHistory && searchHistory.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Searches</CardTitle>
              <Button variant="ghost" size="sm" onClick={clearAllHistory}>
                Clear All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {searchHistory.map((entry) => (
                <div
                  key={entry.search_id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                  onClick={() => applyHistoryEntry(entry)}
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {entry.query || 'No query'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {entry.results_count} results • {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryEntry(entry.search_id);
                    }}
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Free-text Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Query
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={filters.query}
                  onChange={(e) => setFilters({ ...filters, query: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch(1)}
                  placeholder="Search in log messages..."
                  className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <svg
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Filter Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Log Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Log Level
                </label>
                <select
                  value={filters.level}
                  onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Levels</option>
                  {LOG_LEVELS.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </select>
              </div>

              {/* Service */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Service / Application
                </label>
                <input
                  type="text"
                  value={filters.service}
                  onChange={(e) => setFilters({ ...filters, service: e.target.value })}
                  placeholder="Filter by service..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Environment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Environment
                </label>
                <select
                  value={filters.environment}
                  onChange={(e) => setFilters({ ...filters, environment: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Environments</option>
                  {ENVIRONMENTS.map((env) => (
                    <option key={env} value={env}>
                      {env.charAt(0).toUpperCase() + env.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Source */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Source
                </label>
                <input
                  type="text"
                  value={filters.source}
                  onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                  placeholder="Filter by source..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Date
                </label>
                <DatePicker
                  value={filters.startDate}
                  onChange={(date) => setFilters({ ...filters, startDate: date })}
                  placeholder="Select start date"
                  maxDate={filters.endDate || undefined}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  End Date
                </label>
                <DatePicker
                  value={filters.endDate}
                  onChange={(date) => setFilters({ ...filters, endDate: date })}
                  placeholder="Select end date"
                  minDate={filters.startDate || undefined}
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <Button onClick={() => handleSearch(1)} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Searching...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Search
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={handleReset}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reset Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" title="Search Error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {(results.length > 0 || isLoading) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                Search Results
                {totalResults > 0 && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    ({totalResults.toLocaleString()} total)
                  </span>
                )}
              </CardTitle>
              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(currentPage - 1)}
                    disabled={currentPage === 1 || isLoading}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(currentPage + 1)}
                    disabled={currentPage === totalPages || isLoading}
                  >
                    Next
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <SearchableTable
              columns={tableColumns}
              data={results}
              loading={isLoading}
              pageSize={PAGE_SIZE}
              exportable
              rowKey="_id"
              onRowClick={(log) => setSelectedLog(log)}
            />
          </CardContent>
        </Card>
      )}

      {/* No Results */}
      {!isLoading && results.length === 0 && totalResults === 0 && (
        <div className="text-center py-12">
          <svg
            className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No logs found
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Try adjusting your search filters or upload some log files first.
          </p>
        </div>
      )}

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Log Details</h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Timestamp</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {new Date(selectedLog['@timestamp'] || selectedLog.timestamp).toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Level</dt>
                  <dd className="mt-1">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      {
                        debug: 'bg-gray-200 text-gray-700',
                        info: 'bg-blue-100 text-blue-700',
                        warning: 'bg-yellow-100 text-yellow-700',
                        error: 'bg-red-100 text-red-700',
                        critical: 'bg-red-200 text-red-800',
                      }[(selectedLog.level || 'info').toLowerCase()] || 'bg-gray-200 text-gray-700'
                    }`}>
                      {selectedLog.level?.toUpperCase() || 'INFO'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Service</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {selectedLog.service_name || '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Source</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {selectedLog.source || '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Environment</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {selectedLog.environment || '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Message</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-900 p-3 rounded-lg font-mono whitespace-pre-wrap break-words">
                    {selectedLog.message}
                  </dd>
                </div>
              </dl>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
              <Button variant="outline" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
