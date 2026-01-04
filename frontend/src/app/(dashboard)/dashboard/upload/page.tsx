'use client';

import { useState } from 'react';
import LogFileUpload from '@/components/dashboard/LogFileUpload';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui';
import { Alert, Button } from '@/components/ui';
import { logsApi } from '@/lib/api';

interface UploadMetadata {
  source: string;
  environment: string;
  service_name: string;
  tags: string;
}

interface RecentUpload {
  id: string;
  filename: string;
  size: number;
  lines: number;
  timestamp: Date;
  status: 'success' | 'processing' | 'error';
}

const environments = ['development', 'staging', 'production', 'testing'];
const sources = ['application', 'system', 'security', 'access', 'error', 'audit', 'custom'];

export default function EnhancedUploadPage() {
  const [metadata, setMetadata] = useState<UploadMetadata>({
    source: '',
    environment: '',
    service_name: '',
    tags: '',
  });
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setMetadata((prev) => ({ ...prev, [name]: value }));
  };

  const handleUploadComplete = (results: { success: number; failed: number }) => {
    if (results.success > 0) {
      setShowSuccess(true);
      // Add to recent uploads
      setRecentUploads((prev) => [
        {
          id: Date.now().toString(),
          filename: `${results.success} file(s)`,
          size: 0,
          lines: 0,
          timestamp: new Date(),
          status: 'success',
        },
        ...prev.slice(0, 9),
      ]);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Upload Log Files</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Upload your log files for analysis and monitoring
        </p>
      </div>

      {showSuccess && (
        <Alert
          variant="success"
          title="Upload Successful"
          dismissible
          onDismiss={() => setShowSuccess(false)}
        >
          Your log files have been uploaded and are being processed. You can view them in the Analytics dashboard.
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Metadata Card */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Configuration</CardTitle>
              <CardDescription>
                Set metadata for your log files (optional but recommended)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Source
                  </label>
                  <select
                    name="source"
                    value={metadata.source}
                    onChange={handleMetadataChange}
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select source...</option>
                    {sources.map((source) => (
                      <option key={source} value={source}>
                        {source.charAt(0).toUpperCase() + source.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Environment
                  </label>
                  <select
                    name="environment"
                    value={metadata.environment}
                    onChange={handleMetadataChange}
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select environment...</option>
                    {environments.map((env) => (
                      <option key={env} value={env}>
                        {env.charAt(0).toUpperCase() + env.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Service Name
                  </label>
                  <input
                    type="text"
                    name="service_name"
                    value={metadata.service_name}
                    onChange={handleMetadataChange}
                    placeholder="e.g., api-gateway, auth-service"
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tags
                  </label>
                  <input
                    type="text"
                    name="tags"
                    value={metadata.tags}
                    onChange={handleMetadataChange}
                    placeholder="Comma-separated tags"
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upload Component */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Files</CardTitle>
              <CardDescription>
                Drag and drop log files or click to browse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LogFileUpload
                onUploadComplete={handleUploadComplete}
                maxFileSize={100}
                maxFiles={10}
                acceptedFormats={['.log', '.txt', '.json', '.csv', '.ndjson']}
                metadata={metadata}
              />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Supported Formats Card */}
          <Card>
            <CardHeader>
              <CardTitle>Supported Formats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { ext: '.log', desc: 'Standard log files', icon: '📄' },
                  { ext: '.txt', desc: 'Plain text logs', icon: '📝' },
                  { ext: '.json', desc: 'JSON formatted logs', icon: '🔷' },
                  { ext: '.ndjson', desc: 'Newline-delimited JSON', icon: '📊' },
                  { ext: '.csv', desc: 'CSV log exports', icon: '📈' },
                ].map((format) => (
                  <div key={format.ext} className="flex items-center gap-3">
                    <span className="text-xl">{format.icon}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {format.ext}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{format.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Upload Tips */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Max file size: 100MB per file</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Upload up to 10 files at once</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Files are validated before upload</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span>Auto-detection of log formats</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">ℹ</span>
                  <span>Add metadata for better organization</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Recent Uploads */}
          {recentUploads.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Uploads</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentUploads.slice(0, 5).map((upload) => (
                    <div
                      key={upload.id}
                      className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="flex items-center gap-2">
                        {upload.status === 'success' ? (
                          <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        ) : upload.status === 'processing' ? (
                          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        )}
                        <span className="text-sm text-gray-700 dark:text-gray-300 truncate max-w-[120px]">
                          {upload.filename}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {upload.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
