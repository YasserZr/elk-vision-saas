'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { logsApi, healthApi } from '@/lib/api';
import { useNotifications } from '@/hooks/useWebSocket';
import { Notification } from '@/lib/websocket';
import { ChartContainer, DonutChart, Sparkline } from '@/components/dashboard/Charts';

interface DashboardStats {
  total_logs: number;
  total_uploads: number;
  by_source: Record<string, number>;
  by_source_detailed?: Array<{
    file_name: string;
    source: string;
    environment: string;
    service_name: string;
    log_count: number;
    file_size: number;
  }>;
  by_environment: Record<string, number>;
  by_level: Record<string, number>;
  timeline: Array<{ date: string; count: number }>;
}

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    api: { status: string; latency_ms: number };
    elasticsearch: { status: string; latency_ms: number };
    mongodb: { status: string; latency_ms: number };
    redis: { status: string; latency_ms: number };
    logstash: { status: string; latency_ms: number };
  };
}

function StatCard({
  title,
  value,
  icon,
  trend,
  color = 'blue',
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: { value: number; label: string };
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}) {
  const colorClasses = {
    blue: 'bg-blue-500 dark:bg-blue-600',
    green: 'bg-green-500 dark:bg-green-600',
    yellow: 'bg-yellow-500 dark:bg-yellow-600',
    red: 'bg-red-500 dark:bg-red-600',
    purple: 'bg-purple-500 dark:bg-purple-600',
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          {trend && (
            <p className={`text-sm mt-2 ${trend.value >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
            </p>
          )}
        </div>
        <div className={`w-12 h-12 ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function ServiceStatus({ name, status, latency }: { name: string; status: string; latency: number }) {
  const statusColors = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    unhealthy: 'bg-red-500',
  };

  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <div className="flex items-center gap-3">
        <div className={`w-2.5 h-2.5 rounded-full ${statusColors[status as keyof typeof statusColors] || 'bg-gray-400'}`} />
        <span className="font-medium text-gray-700 dark:text-gray-300">{name}</span>
      </div>
      <span className="text-sm text-gray-500 dark:text-gray-400">{latency}ms</span>
    </div>
  );
}

function QuickAction({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
    >
      <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600 dark:text-blue-400 flex-shrink-0">
        {icon}
      </div>
      <div>
        <h4 className="font-medium text-gray-900 dark:text-white">{title}</h4>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, healthRes] = await Promise.allSettled([
        logsApi.getStats(),
        healthApi.check(),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value as unknown as DashboardStats);
      }
      if (healthRes.status === 'fulfilled') {
        setHealth(healthRes.value as unknown as SystemHealth);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Listen for upload notifications and refresh dashboard
  useNotifications((notification: Notification) => {
    if (notification.type === 'upload_status') {
      const uploadData = notification.data;
      
      // Show notification based on status
      if (uploadData?.status === 'completed') {
        console.log('Upload completed:', uploadData);
        // Refresh dashboard data
        fetchData();
      } else if (uploadData?.status === 'processing') {
        console.log('Upload processing:', uploadData);
      }
    } else if (notification.type === 'new_log' || notification.type === 'log_batch') {
      // Refresh when new logs are ingested
      console.log('New logs detected, refreshing dashboard');
      fetchData();
    }
  });

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.first_name || 'User'}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Here&apos;s what&apos;s happening with your logs today.
          </p>
        </div>
        <Link
          href="/dashboard/upload"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload Logs
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Logs"
          value={formatNumber(stats?.total_logs || 0)}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          trend={{ value: 12, label: 'vs last week' }}
          color="blue"
        />
        <StatCard
          title="Total Uploads"
          value={formatNumber(stats?.total_uploads || 0)}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          }
          color="green"
        />
        <StatCard
          title="Error Logs"
          value={formatNumber(stats?.by_level?.error || 0)}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
          trend={{ value: -5, label: 'vs last week' }}
          color="red"
        />
        <StatCard
          title="Warning Logs"
          value={formatNumber(stats?.by_level?.warning || 0)}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="yellow"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">System Health</h3>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                health?.status === 'healthy'
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                  : health?.status === 'degraded'
                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
              }`}
            >
              {health?.status || 'Unknown'}
            </span>
          </div>
          <div className="space-y-1">
            {health?.services ? (
              Object.entries(health.services).map(([name, service]) => (
                <ServiceStatus
                  key={name}
                  name={name.charAt(0).toUpperCase() + name.slice(1)}
                  status={service.status}
                  latency={service.latency_ms}
                />
              ))
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">Unable to fetch health status</p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <QuickAction
              href="/dashboard/upload"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              }
              title="Upload Logs"
              description="Import new log files for analysis"
            />
            <QuickAction
              href="/dashboard/search"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
              title="Search Logs"
              description="Find specific log entries"
            />
            <QuickAction
              href="/dashboard/analytics"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              title="View Analytics"
              description="Explore insights and trends"
            />
            <QuickAction
              href="/dashboard/alerts"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              }
              title="Configure Alerts"
              description="Set up monitoring rules"
            />
            <QuickAction
              href="/dashboard/settings"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              }
              title="Settings"
              description="Manage your preferences"
            />
          </div>
        </div>
      </div>

      {/* Summary Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Log Level Distribution Chart */}
        <ChartContainer title="Log Level Distribution" description="Breakdown by severity">
          {stats?.by_level && Object.keys(stats.by_level).length > 0 ? (
            <DonutChart
              data={[
                { label: 'Debug', value: stats.by_level.debug || 0, color: '#6b7280' },
                { label: 'Info', value: stats.by_level.info || 0, color: '#3b82f6' },
                { label: 'Warning', value: stats.by_level.warning || 0, color: '#f59e0b' },
                { label: 'Error', value: stats.by_level.error || 0, color: '#ef4444' },
                { label: 'Critical', value: stats.by_level.critical || 0, color: '#991b1b' },
              ].filter(d => d.value > 0)}
              centerLabel="Total"
            />
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400">
              No log level data available
            </div>
          )}
        </ChartContainer>

        {/* Timeline Chart */}
        <ChartContainer title="Log Activity Timeline" description="Logs over time">
          {stats?.timeline && stats.timeline.length > 0 ? (
            <div className="space-y-4">
              <Sparkline
                data={stats.timeline.map(d => d.count)}
                color="#3b82f6"
                height={100}
                showArea={true}
              />
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>{stats.timeline[0]?.date}</span>
                <span>{stats.timeline[stats.timeline.length - 1]?.date}</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400">
              No timeline data available
            </div>
          )}
        </ChartContainer>
      </div>

      {/* Log Sources Distribution */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Log Sources</h3>
        {stats?.by_source_detailed && stats.by_source_detailed.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    File Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Log Count
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    File Size
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Service
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Environment
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {stats.by_source_detailed.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                      {item.file_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                        {formatNumber(item.log_count)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {formatFileSize(item.file_size)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {item.source || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {item.service_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                        item.environment === 'production' 
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                          : item.environment === 'staging'
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                      }`}>
                        {item.environment || 'unknown'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : stats?.by_source && Object.keys(stats.by_source).length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(stats.by_source).map(([source, count]) => (
              <div
                key={source}
                className="text-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
              >
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatNumber(count)}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 capitalize">{source}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <svg
              className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-gray-500 dark:text-gray-400">No log data available yet</p>
            <Link
              href="/dashboard/upload"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium mt-2 inline-block"
            >
              Upload your first logs →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
