'use client';

import React, { useCallback, useState, useRef, useEffect } from 'react';
import { Button, Alert, Spinner } from '@/components/ui';
import { logsApi } from '@/lib/api';

export interface LogFile {
  file: File;
  id: string;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: 'pending' | 'validating' | 'uploading' | 'processing' | 'success' | 'error';
  error?: string;
  validationResult?: {
    isValid: boolean;
    lineCount: number;
    format: string;
    errors: string[];
  };
}

export interface LogFileUploadProps {
  onUploadComplete?: (results: { success: number; failed: number }) => void;
  maxFileSize?: number; // MB
  maxFiles?: number;
  acceptedFormats?: string[];
}

const ACCEPTED_FORMATS = ['.log', '.txt', '.json', '.csv', '.ndjson'];
const MAX_FILE_SIZE_MB = 100;

export default function LogFileUpload({
  onUploadComplete,
  maxFileSize = MAX_FILE_SIZE_MB,
  maxFiles = 10,
  acceptedFormats = ACCEPTED_FORMATS,
}: LogFileUploadProps) {
  const [files, setFiles] = useState<LogFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStats, setUploadStats] = useState<{ success: number; failed: number } | null>(null);
  const [metadata, setMetadata] = useState({
    source: '',
    environment: '',
    serviceName: '',
    tags: [] as string[],
  });
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const generateId = () => `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getFileExtension = (filename: string): string => {
    return '.' + filename.split('.').pop()?.toLowerCase();
  };

  const detectLogFormat = async (file: File): Promise<string> => {
    const text = await file.slice(0, 4096).text();
    
    // Try to detect JSON
    try {
      JSON.parse(text.split('\n')[0]);
      return 'json';
    } catch {}

    // Check for NDJSON
    const lines = text.split('\n').filter(l => l.trim());
    if (lines.length > 1) {
      try {
        lines.slice(0, 3).forEach(line => JSON.parse(line));
        return 'ndjson';
      } catch {}
    }

    // Check for CSV
    if (text.includes(',') && lines[0].split(',').length > 2) {
      return 'csv';
    }

    // Check for common log formats
    if (/^\d{4}-\d{2}-\d{2}/.test(text) || /^\[\d{4}/.test(text)) {
      return 'structured-log';
    }

    return 'plain-text';
  };

  const validateFile = async (logFile: LogFile): Promise<LogFile> => {
    const { file } = logFile;
    const errors: string[] = [];

    // Check file extension
    const ext = getFileExtension(file.name);
    if (!acceptedFormats.includes(ext) && !acceptedFormats.includes('*')) {
      errors.push(`File type "${ext}" is not supported. Accepted: ${acceptedFormats.join(', ')}`);
    }

    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      errors.push(`File size (${formatFileSize(file.size)}) exceeds the ${maxFileSize}MB limit`);
    }

    // Check if file is empty
    if (file.size === 0) {
      errors.push('File is empty');
    }

    // Detect format and count lines
    let lineCount = 0;
    let format = 'unknown';
    
    if (errors.length === 0) {
      try {
        format = await detectLogFormat(file);
        const text = await file.text();
        lineCount = text.split('\n').filter(l => l.trim()).length;
        
        if (lineCount === 0) {
          errors.push('File contains no valid log entries');
        }
      } catch (err) {
        errors.push('Failed to read file contents');
      }
    }

    return {
      ...logFile,
      status: errors.length > 0 ? 'error' : 'pending',
      error: errors.length > 0 ? errors[0] : undefined,
      validationResult: {
        isValid: errors.length === 0,
        lineCount,
        format,
        errors,
      },
    };
  };

  const addFiles = async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    if (files.length + fileArray.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed. You can add ${maxFiles - files.length} more.`);
      return;
    }

    // Create initial file objects
    const logFiles: LogFile[] = fileArray.map((file) => ({
      file,
      id: generateId(),
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
      progress: 0,
      status: 'validating' as const,
    }));

    setFiles((prev) => [...prev, ...logFiles]);

    // Validate files
    for (const logFile of logFiles) {
      const validated = await validateFile(logFile);
      setFiles((prev) =>
        prev.map((f) => (f.id === logFile.id ? validated : f))
      );
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  }, [files.length]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      addFiles(selectedFiles);
    }
    e.target.value = '';
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadFile = async (logFile: LogFile): Promise<boolean> => {
    try {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === logFile.id ? { ...f, status: 'uploading' as const, progress: 0 } : f
        )
      );

      // Simulate progress for demo (replace with actual upload progress)
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === logFile.id && f.status === 'uploading'
              ? { ...f, progress: Math.min(f.progress + 10, 90) }
              : f
          )
        );
      }, 200);

      // Upload using the logsApi with proper parameters
      await logsApi.upload(
        [logFile.file],
        {
          source: metadata.source || undefined,
          environment: metadata.environment || undefined,
          service_name: metadata.serviceName || undefined,
          tags: metadata.tags.length > 0 ? metadata.tags : undefined,
        },
        (progress) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === logFile.id ? { ...f, progress } : f
            )
          );
        }
      );

      clearInterval(progressInterval);

      setFiles((prev) =>
        prev.map((f) =>
          f.id === logFile.id
            ? { ...f, status: 'success' as const, progress: 100 }
            : f
        )
      );

      return true;
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === logFile.id
            ? {
                ...f,
                status: 'error' as const,
                error: error instanceof Error ? error.message : 'Upload failed',
              }
            : f
        )
      );
      return false;
    }
  };

  const handleUpload = async () => {
    const validFiles = files.filter(
      (f) => f.status === 'pending' && f.validationResult?.isValid
    );
    
    if (validFiles.length === 0) return;

    setIsUploading(true);
    setUploadStats(null);
    abortControllerRef.current = new AbortController();

    let success = 0;
    let failed = 0;

    for (const file of validFiles) {
      if (abortControllerRef.current?.signal.aborted) break;
      
      const result = await uploadFile(file);
      if (result) success++;
      else failed++;
    }

    setIsUploading(false);
    setUploadStats({ success, failed });
    onUploadComplete?.({ success, failed });
  };

  const cancelUpload = () => {
    abortControllerRef.current?.abort();
    setIsUploading(false);
    setFiles((prev) =>
      prev.map((f) =>
        f.status === 'uploading' ? { ...f, status: 'pending' as const, progress: 0 } : f
      )
    );
  };

  const clearAll = () => {
    setFiles([]);
    setUploadStats(null);
  };

  const pendingFiles = files.filter((f) => f.status === 'pending' && f.validationResult?.isValid);
  const hasErrors = files.some((f) => f.status === 'error');
  const hasCompleted = files.some((f) => f.status === 'success');

  const getStatusIcon = (status: LogFile['status']) => {
    switch (status) {
      case 'validating':
        return <Spinner size="sm" />;
      case 'uploading':
      case 'processing':
        return <Spinner size="sm" />;
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getFormatBadge = (format: string) => {
    const colors: Record<string, string> = {
      json: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      ndjson: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      csv: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      'structured-log': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      'plain-text': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
    };
    return colors[format] || colors['plain-text'];
  };

  return (
    <div className="space-y-4">
      {/* Upload Stats Alert */}
      {uploadStats && (
        <Alert
          variant={uploadStats.failed > 0 ? 'warning' : 'success'}
          title="Upload Complete"
          dismissible
          onDismiss={() => setUploadStats(null)}
        >
          {uploadStats.success} file{uploadStats.success !== 1 ? 's' : ''} uploaded successfully
          {uploadStats.failed > 0 && `, ${uploadStats.failed} failed`}.
        </Alert>
      )}

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200
          ${isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-[1.02]'
            : 'border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600 hover:bg-gray-50 dark:hover:bg-gray-800/50'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        role="button"
        tabIndex={isUploading ? -1 : 0}
        onKeyDown={(e) => {
          if (!isUploading && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        aria-label="Drop log files here or click to browse"
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={isUploading}
        />

        <div className="flex flex-col items-center gap-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors ${
            isDragging ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-gray-100 dark:bg-gray-800'
          }`}>
            <svg
              className={`w-8 h-8 transition-colors ${
                isDragging ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              {isDragging ? 'Drop your log files here' : 'Drag & drop log files'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              or <span className="text-blue-600 dark:text-blue-400 font-medium">browse</span> to select files
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-400 dark:text-gray-500">
            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
              Max {maxFileSize}MB per file
            </span>
            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
              Up to {maxFiles} files
            </span>
            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
              {acceptedFormats.join(', ')}
            </span>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {files.length} file{files.length !== 1 ? 's' : ''} • {pendingFiles.length} ready to upload
            </span>
            <div className="flex items-center gap-2">
              {hasCompleted && (
                <button
                  onClick={() => setFiles((prev) => prev.filter((f) => f.status !== 'success'))}
                  className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  Clear completed
                </button>
              )}
              <button
                onClick={clearAll}
                className="text-sm text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
              >
                Clear all
              </button>
            </div>
          </div>

          {/* File Items */}
          <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-80 overflow-y-auto">
            {files.map((logFile) => (
              <div
                key={logFile.id}
                className={`p-4 transition-colors ${
                  logFile.status === 'error' ? 'bg-red-50/50 dark:bg-red-900/10' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Status Icon */}
                  <div className="flex-shrink-0 mt-0.5">{getStatusIcon(logFile.status)}</div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {logFile.name}
                      </p>
                      {logFile.validationResult?.format && (
                        <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${getFormatBadge(logFile.validationResult.format)}`}>
                          {logFile.validationResult.format}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                      <span>{formatFileSize(logFile.size)}</span>
                      {(logFile.validationResult?.lineCount ?? 0) > 0 && (
                        <span>{logFile.validationResult?.lineCount?.toLocaleString()} lines</span>
                      )}
                      {logFile.status === 'uploading' && (
                        <span className="text-blue-600 dark:text-blue-400">
                          Uploading... {logFile.progress}%
                        </span>
                      )}
                      {logFile.status === 'processing' && (
                        <span className="text-purple-600 dark:text-purple-400">Processing...</span>
                      )}
                    </div>

                    {/* Progress Bar */}
                    {(logFile.status === 'uploading' || logFile.status === 'processing') && (
                      <div className="mt-2 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            logFile.status === 'processing'
                              ? 'bg-purple-500 animate-pulse'
                              : 'bg-blue-500'
                          }`}
                          style={{ width: `${logFile.progress}%` }}
                        />
                      </div>
                    )}

                    {/* Error Message */}
                    {logFile.error && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400">{logFile.error}</p>
                    )}
                  </div>

                  {/* Remove Button */}
                  {logFile.status !== 'uploading' && logFile.status !== 'processing' && (
                    <button
                      onClick={() => removeFile(logFile.id)}
                      className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                      aria-label={`Remove ${logFile.name}`}
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-800">
            {isUploading ? (
              <Button variant="danger" onClick={cancelUpload}>
                Cancel Upload
              </Button>
            ) : (
              <Button
                onClick={handleUpload}
                disabled={pendingFiles.length === 0}
                isLoading={isUploading}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Upload {pendingFiles.length} File{pendingFiles.length !== 1 ? 's' : ''}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
