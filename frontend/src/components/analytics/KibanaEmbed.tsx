'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui';

export interface KibanaEmbedProps {
  dashboardId?: string;
  kibanaUrl?: string;
  title?: string;
  height?: number;
  filters?: Record<string, string>;
  timeRange?: {
    from: string;
    to: string;
  };
  refreshInterval?: number;
  className?: string;
}

export function KibanaEmbed({
  dashboardId,
  kibanaUrl = process.env.NEXT_PUBLIC_KIBANA_URL || 'http://localhost:5601',
  title = 'Kibana Dashboard',
  height = 600,
  filters = {},
  timeRange,
  refreshInterval,
  className = '',
}: KibanaEmbedProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build Kibana embed URL
  const buildEmbedUrl = () => {
    if (!dashboardId) return null;

    // Kibana 8.x embed URL format - match the working dashboard URL
    const baseUrl = `${kibanaUrl}/app/dashboards#/view/${dashboardId}`;
    
    // Use exact format that works: _g parameter with RISON notation (not URL encoded)
    // embed=true enables iframe embedding
    return `${baseUrl}?embed=true&_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15d,to:now))`;
  };

  const embedUrl = buildEmbedUrl();

  if (!dashboardId) {
    return (
      <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-8 ${className}`}>
        <div className="text-center">
          <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Dashboard Selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Configure a Kibana dashboard ID to embed visualizations here.
          </p>
          <Button variant="outline" onClick={() => window.open(kibanaUrl, '_blank')}>
            Open Kibana
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsLoading(true);
              setError(null);
            }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(embedUrl || kibanaUrl, '_blank')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Iframe */}
      <div className="relative" style={{ height }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-800">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">Loading dashboard...</p>
            </div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50 dark:bg-red-900/20">
            <div className="text-center">
              <svg className="w-12 h-12 text-red-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}
        <iframe
          src={embedUrl || ''}
          className="w-full h-full border-0"
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setIsLoading(false);
            setError('Failed to load Kibana dashboard');
          }}
          title={title}
          allowFullScreen
        />
      </div>
    </div>
  );
}

// Quick visualization cards that link to Kibana
export interface KibanaVisualizationCardProps {
  title: string;
  description?: string;
  visualizationId: string;
  kibanaUrl?: string;
  thumbnail?: string;
  onClick?: () => void;
}

export function KibanaVisualizationCard({
  title,
  description,
  visualizationId,
  kibanaUrl = process.env.NEXT_PUBLIC_KIBANA_URL || 'http://localhost:5601',
  thumbnail,
  onClick,
}: KibanaVisualizationCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      window.open(`${kibanaUrl}/app/visualize#/edit/${visualizationId}`, '_blank');
    }
  };

  return (
    <button
      onClick={handleClick}
      className="w-full text-left bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-700 transition-all duration-200"
    >
      {thumbnail ? (
        <img src={thumbnail} alt={title} className="w-full h-32 object-cover" />
      ) : (
        <div className="w-full h-32 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <svg className="w-12 h-12 text-white/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
      )}
      <div className="p-4">
        <h4 className="font-semibold text-gray-900 dark:text-white">{title}</h4>
        {description && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{description}</p>
        )}
      </div>
    </button>
  );
}

export default KibanaEmbed;
