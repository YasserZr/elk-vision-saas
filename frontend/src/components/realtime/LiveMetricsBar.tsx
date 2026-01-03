/**
 * Live Metrics Bar Component
 * 
 * Displays real-time metrics in a compact bar format:
 * - Logs per second
 * - Errors per minute
 * - Connected users
 * - Connection status indicator
 */

'use client';

import React from 'react';
import { useMetrics } from '@/hooks/useMetrics';

interface LiveMetricsBarProps {
    className?: string;
    compact?: boolean;
}

export default function LiveMetricsBar({ className = '', compact = false }: LiveMetricsBarProps) {
    const { isConnected, metrics } = useMetrics();

    // Animated counter component
    const AnimatedNumber = ({ value, suffix = '' }: { value: number; suffix?: string }) => (
        <span className="font-mono font-bold tabular-nums transition-all duration-300">
            {value.toLocaleString()}{suffix}
        </span>
    );

    if (compact) {
        return (
            <div className={`flex items-center gap-4 text-sm ${className}`}>
                {/* Connection indicator */}
                <div className="flex items-center gap-1.5">
                    <span
                        className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                            }`}
                    />
                    <span className="text-gray-500 dark:text-gray-400">
                        {isConnected ? 'Live' : 'Offline'}
                    </span>
                </div>

                {metrics && (
                    <>
                        <span className="text-gray-300 dark:text-gray-600">|</span>
                        <span className="text-gray-600 dark:text-gray-300">
                            <AnimatedNumber value={metrics.logs_per_second} suffix="/s" />
                        </span>
                        {metrics.errors_per_minute > 0 && (
                            <>
                                <span className="text-gray-300 dark:text-gray-600">|</span>
                                <span className="text-red-500">
                                    <AnimatedNumber value={metrics.errors_per_minute} /> errors
                                </span>
                            </>
                        )}
                    </>
                )}
            </div>
        );
    }

    return (
        <div className={`bg-gray-900 dark:bg-gray-950 border-b border-gray-800 ${className}`}>
            <div className="px-4 py-2 flex items-center justify-between">
                {/* Left: Connection status */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <span
                            className={`w-2.5 h-2.5 rounded-full ${isConnected
                                    ? 'bg-green-500 animate-pulse shadow-lg shadow-green-500/50'
                                    : 'bg-gray-500'
                                }`}
                        />
                        <span className="text-sm font-medium text-gray-300">
                            {isConnected ? 'Live' : 'Connecting...'}
                        </span>
                    </div>
                </div>

                {/* Center: Metrics */}
                {metrics && (
                    <div className="flex items-center gap-6">
                        {/* Logs per second */}
                        <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span className="text-gray-400 text-sm">Logs:</span>
                            <span className="text-white font-mono font-bold">
                                <AnimatedNumber value={metrics.logs_per_second} suffix="/s" />
                            </span>
                        </div>

                        {/* Errors per minute */}
                        <div className="flex items-center gap-2">
                            <svg className={`w-4 h-4 ${metrics.errors_per_minute > 0 ? 'text-red-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-gray-400 text-sm">Errors:</span>
                            <span className={`font-mono font-bold ${metrics.errors_per_minute > 0 ? 'text-red-400' : 'text-gray-500'}`}>
                                <AnimatedNumber value={metrics.errors_per_minute} suffix="/min" />
                            </span>
                        </div>

                        {/* Warnings per minute */}
                        {metrics.warnings_per_minute > 0 && (
                            <div className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                <span className="text-gray-400 text-sm">Warnings:</span>
                                <span className="text-yellow-400 font-mono font-bold">
                                    <AnimatedNumber value={metrics.warnings_per_minute} suffix="/min" />
                                </span>
                            </div>
                        )}
                    </div>
                )}

                {/* Right: Connected users */}
                <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <span className="text-gray-400 text-sm">Users:</span>
                    <span className="text-purple-400 font-mono font-bold">
                        {metrics?.connected_users ?? 0}
                    </span>
                </div>
            </div>
        </div>
    );
}
