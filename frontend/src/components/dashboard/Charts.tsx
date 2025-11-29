'use client';

import React from 'react';

export interface ChartContainerProps {
  children: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function ChartContainer({
  children,
  title,
  description,
  action,
  className = '',
}: ChartContainerProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 ${className}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          {description && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="relative">{children}</div>
    </div>
  );
}

// Simple bar chart component
export interface SimpleBarChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  maxValue?: number;
  showValues?: boolean;
  className?: string;
}

export function SimpleBarChart({
  data,
  maxValue,
  showValues = true,
  className = '',
}: SimpleBarChartProps) {
  const max = maxValue || Math.max(...data.map((d) => d.value)) || 1;

  return (
    <div className={`space-y-3 ${className}`}>
      {data.map((item, index) => (
        <div key={index} className="flex items-center gap-3">
          <span className="text-sm text-gray-600 dark:text-gray-400 w-24 truncate">
            {item.label}
          </span>
          <div className="flex-1 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
            <div
              className={`h-full rounded-lg transition-all duration-500 ${
                item.color || 'bg-blue-500'
              }`}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          {showValues && (
            <span className="text-sm font-medium text-gray-900 dark:text-white w-16 text-right">
              {item.value.toLocaleString()}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// Donut/Pie chart data display
export interface DonutChartProps {
  data: Array<{ label: string; value: number; color: string }>;
  total?: number;
  centerLabel?: string;
  className?: string;
}

export function DonutChart({
  data,
  total,
  centerLabel = 'Total',
  className = '',
}: DonutChartProps) {
  const totalValue = total || data.reduce((sum, item) => sum + item.value, 0);

  // Calculate percentages
  const dataWithPercent = data.map((item) => ({
    ...item,
    percent: totalValue > 0 ? (item.value / totalValue) * 100 : 0,
  }));

  return (
    <div className={`flex items-center gap-6 ${className}`}>
      {/* Donut visual */}
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
          {(() => {
            let cumulativePercent = 0;
            return dataWithPercent.map((item, index) => {
              const strokeDasharray = `${item.percent * 2.51327} ${251.327}`;
              const strokeDashoffset = -cumulativePercent * 2.51327;
              cumulativePercent += item.percent;
              return (
                <circle
                  key={index}
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke={item.color}
                  strokeWidth="12"
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-500"
                />
              );
            });
          })()}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {totalValue.toLocaleString()}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {centerLabel}
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1 space-y-2">
        {dataWithPercent.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {item.label}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {item.value.toLocaleString()}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                ({item.percent.toFixed(1)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Timeline/Sparkline chart
export interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  showArea?: boolean;
  className?: string;
}

export function Sparkline({
  data,
  color = '#3b82f6',
  height = 40,
  showArea = true,
  className = '',
}: SparklineProps) {
  if (data.length === 0) return null;

  const max = Math.max(...data) || 1;
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `${pathD} L 100,${height} L 0,${height} Z`;

  return (
    <svg
      className={className}
      viewBox={`0 0 100 ${height}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height }}
    >
      {showArea && (
        <path d={areaD} fill={color} fillOpacity="0.1" />
      )}
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

export default {
  ChartContainer,
  SimpleBarChart,
  DonutChart,
  Sparkline,
};
