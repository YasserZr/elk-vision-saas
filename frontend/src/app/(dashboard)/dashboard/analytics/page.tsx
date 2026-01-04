'use client';

import { useEffect, useState, useMemo } from 'react';
import { logsApi } from '@/lib/api';
import {
  TimeSeriesChart,
  BarChart,
  DoughnutChart,
  ChartCard,
} from '@/components/analytics/RechartsComponents';
import { KPIGrid, KPIIcons } from '@/components/analytics/KPICard';
import SearchableTable, { Column } from '@/components/analytics/SearchableTable';
import { KibanaEmbed } from '@/components/analytics/KibanaEmbed';
import { Button, Alert, Spinner } from '@/components/ui';

interface LogStats {
  total_logs: number;
  total_uploads: number;
  by_source: Record<string, number>;
  by_environment: Record<string, number>;
  by_level: Record<string, number>;
  timeline: Array<{ date: string; count: number }>;
}

interface LogEntry {
  _id: string;
  timestamp: string;
  level: string;
  message: string;
  source: string;
  environment: string;
  service_name?: string;
  [key: string]: unknown; // Index signature for Record compatibility
}

const levelColors: Record<string, string> = {
  debug: 'rgb(156, 163, 175)',
  info: 'rgb(59, 130, 246)',
  warning: 'rgb(234, 179, 8)',
  error: 'rgb(239, 68, 68)',
  critical: 'rgb(185, 28, 28)',
};

export default function AnalyticsDashboardPage() {
  const [stats, setStats] = useState<LogStats | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'kibana'>('overview');

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsRes, logsRes] = await Promise.allSettled([
        logsApi.getStats(),
        logsApi.search({ page_size: 100 }),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value as unknown as LogStats);
      }
      if (logsRes.status === 'fulfilled') {
        const logsData = logsRes.value as unknown as { results: LogEntry[] };
        setLogs(logsData.results || []);
      }
    } catch (err) {
      setError('Failed to fetch analytics data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // KPI data
  const kpiData = useMemo(() => {
    if (!stats) return [];

    const errorCount = (stats.by_level?.error || 0) + (stats.by_level?.critical || 0);
    const warningCount = stats.by_level?.warning || 0;
    const errorRate = stats.total_logs > 0 ? ((errorCount / stats.total_logs) * 100).toFixed(2) : '0';

    // Generate fake trend data for demo
    const generateTrend = () => Array.from({ length: 20 }, () => Math.random() * 100);

    return [
      {
        title: 'Total Logs',
        value: stats.total_logs,
        change: { value: 12.5, period: 'vs last period' },
        trend: generateTrend(),
        icon: KPIIcons.logs,
        color: 'blue' as const,
      },
      {
        title: 'Error Rate',
        value: `${errorRate}%`,
        change: { value: -3.2, period: 'vs last period' },
        trend: generateTrend(),
        icon: KPIIcons.errors,
        color: 'red' as const,
      },
      {
        title: 'Warnings',
        value: warningCount,
        change: { value: 5.1, period: 'vs last period' },
        trend: generateTrend(),
        icon: KPIIcons.warnings,
        color: 'yellow' as const,
      },
      {
        title: 'Log Sources',
        value: Object.keys(stats.by_source || {}).length,
        icon: KPIIcons.storage,
        color: 'purple' as const,
      },
    ];
  }, [stats]);

  // Chart data transformations
  const timelineChartData = useMemo(() => {
    if (!stats?.timeline) return [];
    return stats.timeline.map((item) => ({
      timestamp: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: item.count,
    }));
  }, [stats]);

  const levelChartData = useMemo(() => {
    if (!stats?.by_level) return [];
    return Object.entries(stats.by_level).map(([label, value]) => ({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      value,
      color: levelColors[label] || 'rgb(107, 114, 128)',
    }));
  }, [stats]);

  const sourceChartData = useMemo(() => {
    if (!stats?.by_source) return [];
    return Object.entries(stats.by_source)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([label, value]) => ({ label, value }));
  }, [stats]);

  const environmentChartData = useMemo(() => {
    if (!stats?.by_environment) return [];
    return Object.entries(stats.by_environment).map(([label, value]) => ({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      value,
    }));
  }, [stats]);

  // Table columns
  const tableColumns: Column<LogEntry>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp',
      sortable: true,
      render: (item) => (
        <span className="text-gray-500 text-xs font-mono">
          {new Date(item.timestamp).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'level',
      header: 'Level',
      sortable: true,
      filterable: true,
      render: (item) => {
        const colors: Record<string, string> = {
          debug: 'bg-gray-100 text-gray-700',
          info: 'bg-blue-100 text-blue-700',
          warning: 'bg-yellow-100 text-yellow-700',
          error: 'bg-red-100 text-red-700',
          critical: 'bg-red-200 text-red-800',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[item.level] || colors.info}`}>
            {item.level?.toUpperCase()}
          </span>
        );
      },
    },
    {
      key: 'message',
      header: 'Message',
      render: (item) => (
        <span className="text-gray-900 dark:text-gray-100 line-clamp-2 text-sm">
          {typeof item.message === 'string' ? item.message : JSON.stringify(item.message)}
        </span>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      sortable: true,
      filterable: true,
      render: (item) => (
        <span className="text-gray-600 dark:text-gray-400 text-sm">{item.source || '-'}</span>
      ),
    },
    {
      key: 'environment',
      header: 'Environment',
      sortable: true,
      filterable: true,
      render: (item) => (
        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">
          {item.environment || '-'}
        </span>
      ),
    },
  ];

  if (isLoading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Monitor and analyze your log data in real-time
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
          <Button variant="outline" onClick={fetchData} disabled={isLoading}>
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex gap-6">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'logs', label: 'Log Explorer', icon: '📋' },
            { id: 'kibana', label: 'Kibana', icon: '🔍' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPIs */}
          <KPIGrid kpis={kpiData} columns={4} loading={isLoading} />

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard
              title="Log Volume Over Time"
              subtitle="Number of log entries per day"
              action={
                <select className="text-sm border-0 bg-gray-100 dark:bg-gray-800 rounded-lg px-2 py-1">
                  <option>Last 7 days</option>
                  <option>Last 30 days</option>
                </select>
              }
            >
              <TimeSeriesChart
                data={timelineChartData}
                label="Log Count"
                height={280}
                fillArea={true}
              />
            </ChartCard>

            <ChartCard title="Log Levels Distribution" subtitle="Breakdown by severity">
              <DoughnutChart
                data={levelChartData}
                height={280}
                centerText={stats?.total_logs?.toLocaleString()}
              />
            </ChartCard>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Top Log Sources" subtitle="Most active log sources">
              <BarChart data={sourceChartData} height={280} horizontal />
            </ChartCard>

            <ChartCard title="Environment Distribution" subtitle="Logs by environment">
              <BarChart data={environmentChartData} height={280} />
            </ChartCard>
          </div>

          {/* Recent Logs Preview */}
          <ChartCard
            title="Recent Log Entries"
            subtitle="Latest 10 log entries"
            action={
              <Button variant="ghost" size="sm" onClick={() => setActiveTab('logs')}>
                View All
              </Button>
            }
          >
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {logs.slice(0, 10).map((log, index) => (
                <div
                  key={log._id || index}
                  className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
                >
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      {
                        debug: 'bg-gray-200 text-gray-700',
                        info: 'bg-blue-100 text-blue-700',
                        warning: 'bg-yellow-100 text-yellow-700',
                        error: 'bg-red-100 text-red-700',
                        critical: 'bg-red-200 text-red-800',
                      }[log.level] || 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {log.level?.toUpperCase()}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                      {typeof log.message === 'string' ? log.message : JSON.stringify(log.message)}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {new Date(log.timestamp).toLocaleString()} • {log.source}
                    </p>
                  </div>
                </div>
              ))}
              {logs.length === 0 && (
                <p className="text-center text-gray-500 py-8">No log entries found</p>
              )}
            </div>
          </ChartCard>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <SearchableTable
          columns={tableColumns}
          data={logs}
          loading={isLoading}
          searchPlaceholder="Search logs by message, source, or environment..."
          pageSize={50}
          exportable
          rowKey="_id"
          onRowClick={(log) => console.log('Selected log:', log)}
        />
      )}

      {/* Kibana Tab */}
      {activeTab === 'kibana' && (
        <div className="space-y-6">
          <Alert variant="info" title="Kibana Integration">
            Connect your Kibana instance to view advanced visualizations and dashboards.
            Set NEXT_PUBLIC_KIBANA_URL and KIBANA_DASHBOARD_ID in your environment variables.
          </Alert>

          <KibanaEmbed
            dashboardId={process.env.NEXT_PUBLIC_KIBANA_DASHBOARD_ID}
            title="Log Analytics Dashboard"
            height={700}
            timeRange={{ from: 'now-24h', to: 'now' }}
          />
        </div>
      )}
    </div>
  );
}
