'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Input, Button, Spinner } from '@/components/ui';

export interface Column<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (item: T, index: number) => React.ReactNode;
}

export interface SearchableTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  searchPlaceholder?: string;
  emptyMessage?: string;
  pageSize?: number;
  onRowClick?: (item: T) => void;
  rowKey?: keyof T | ((item: T, index: number) => string | number);
  stickyHeader?: boolean;
  striped?: boolean;
  className?: string;
  exportable?: boolean;
  onExport?: (data: T[], format: 'csv' | 'json') => void;
}

export default function SearchableTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  searchPlaceholder = 'Search...',
  emptyMessage = 'No results found',
  pageSize = 10,
  onRowClick,
  rowKey,
  stickyHeader = false,
  striped = true,
  className = '',
  exportable = false,
  onExport,
}: SearchableTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>({});

  // Get unique values for filterable columns
  const filterOptions = useMemo(() => {
    const options: Record<string, Set<string>> = {};
    columns
      .filter((col) => col.filterable)
      .forEach((col) => {
        options[String(col.key)] = new Set(
          data.map((item) => String(item[col.key as keyof T] ?? '')).filter(Boolean)
        );
      });
    return options;
  }, [columns, data]);

  // Filter data
  const filteredData = useMemo(() => {
    return data.filter((item) => {
      // Global search
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        const matches = columns.some((col) => {
          const value = item[col.key as keyof T];
          return String(value ?? '').toLowerCase().includes(searchLower);
        });
        if (!matches) return false;
      }

      // Column filters
      for (const [key, filterValue] of Object.entries(columnFilters)) {
        if (filterValue && String(item[key as keyof T]) !== filterValue) {
          return false;
        }
      }

      return true;
    });
  }, [data, searchQuery, columnFilters, columns]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortKey as keyof T];
      const bValue = b[sortKey as keyof T];

      if (aValue === bValue) return 0;
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      let comparison: number;
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue;
      } else {
        comparison = String(aValue).localeCompare(String(bValue));
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortKey, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  // Handlers
  const handleSort = useCallback((key: string) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  }, [sortKey]);

  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  }, []);

  const handleColumnFilter = useCallback((key: string, value: string) => {
    setColumnFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
    setCurrentPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setColumnFilters({});
    setSortKey(null);
    setCurrentPage(1);
  }, []);

  const getRowKey = (item: T, index: number): string | number => {
    if (typeof rowKey === 'function') return rowKey(item, index);
    if (rowKey) return String(item[rowKey]);
    return index;
  };

  const handleExport = (format: 'csv' | 'json') => {
    if (onExport) {
      onExport(sortedData, format);
    } else {
      // Default export
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(sortedData, null, 2)], { type: 'application/json' });
        downloadBlob(blob, 'export.json');
      } else {
        const headers = columns.map((c) => c.header).join(',');
        const rows = sortedData.map((item) =>
          columns.map((col) => `"${String(item[col.key as keyof T] ?? '')}"`).join(',')
        );
        const csv = [headers, ...rows].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        downloadBlob(blob, 'export.csv');
      }
    }
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasActiveFilters = searchQuery || Object.values(columnFilters).some(Boolean);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden ${className}`}>
      {/* Toolbar */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Input
              type="search"
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
            {exportable && (
              <div className="flex items-center gap-1">
                <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  CSV
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleExport('json')}>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  JSON
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Column Filters */}
        {columns.some((c) => c.filterable) && (
          <div className="flex flex-wrap gap-2 mt-3">
            {columns
              .filter((col) => col.filterable)
              .map((col) => (
                <select
                  key={String(col.key)}
                  value={columnFilters[String(col.key)] || ''}
                  onChange={(e) => handleColumnFilter(String(col.key), e.target.value)}
                  className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 border-0 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All {col.header}</option>
                  {Array.from(filterOptions[String(col.key)] || []).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              ))}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className={stickyHeader ? 'sticky top-0 z-10' : ''}>
            <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider ${column.width || ''}`}
                >
                  {column.sortable ? (
                    <button
                      onClick={() => handleSort(String(column.key))}
                      className="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-200 transition-colors group"
                    >
                      {column.header}
                      <span className="flex flex-col">
                        <svg
                          className={`w-3 h-3 -mb-1 transition-colors ${
                            sortKey === column.key && sortDirection === 'asc'
                              ? 'text-blue-500'
                              : 'text-gray-300 dark:text-gray-600 group-hover:text-gray-400'
                          }`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M5 10l5-5 5 5H5z" />
                        </svg>
                        <svg
                          className={`w-3 h-3 transition-colors ${
                            sortKey === column.key && sortDirection === 'desc'
                              ? 'text-blue-500'
                              : 'text-gray-300 dark:text-gray-600 group-hover:text-gray-400'
                          }`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M5 10l5 5 5-5H5z" />
                        </svg>
                      </span>
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-gray-500 dark:text-gray-400"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((item, index) => (
                <tr
                  key={getRowKey(item, index)}
                  onClick={() => onRowClick?.(item)}
                  className={`
                    transition-colors
                    ${onRowClick ? 'cursor-pointer' : ''}
                    ${striped && index % 2 === 1 ? 'bg-gray-50/50 dark:bg-gray-800/30' : ''}
                    hover:bg-gray-100/70 dark:hover:bg-gray-800/70
                  `}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={(e) => {
                    if (onRowClick && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      onRowClick(item);
                    }
                  }}
                >
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100"
                    >
                      {column.render
                        ? column.render(item, index)
                        : String(item[column.key as keyof T] ?? '-')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Button>
            
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              return (
                <Button
                  key={pageNum}
                  variant={currentPage === pageNum ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
