'use client';

import React from 'react';
import { Card } from '@/components/ui';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  icon?: React.ReactNode;
  className?: string;
  loading?: boolean;
}

export default function StatCard({
  title,
  value,
  change,
  icon,
  className = '',
  loading = false,
}: StatCardProps) {
  if (loading) {
    return (
      <Card className={className} hover>
        <div className="animate-pulse">
          <div className="flex items-center justify-between">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24" />
            <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          </div>
          <div className="mt-4 h-8 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          <div className="mt-2 h-4 bg-gray-200 dark:bg-gray-700 rounded w-16" />
        </div>
      </Card>
    );
  }

  return (
    <Card className={className} hover>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
          {title}
        </p>
        {icon && (
          <div className="flex-shrink-0 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
            {icon}
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-gray-900 dark:text-white">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        {change && (
          <div className="flex items-center mt-2">
            {change.type === 'increase' ? (
              <svg
                className="w-4 h-4 text-green-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4 text-red-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            <span
              className={`ml-1 text-sm font-medium ${
                change.type === 'increase'
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {change.value}%
            </span>
            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
              vs last period
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
