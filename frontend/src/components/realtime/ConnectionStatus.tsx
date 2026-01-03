/**
 * Connection Status Component
 * 
 * Displays WebSocket connection status with:
 * - Animated indicator (connected/disconnected/reconnecting)
 * - Manual reconnect button
 * - Connection details on hover
 */

'use client';

import React from 'react';

interface ConnectionStatusProps {
    isConnected: boolean;
    isReconnecting?: boolean;
    lastConnected?: Date;
    onReconnect?: () => void;
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    className?: string;
}

export default function ConnectionStatus({
    isConnected,
    isReconnecting = false,
    lastConnected,
    onReconnect,
    size = 'md',
    showLabel = true,
    className = '',
}: ConnectionStatusProps) {
    const sizeClasses = {
        sm: 'w-2 h-2',
        md: 'w-2.5 h-2.5',
        lg: 'w-3 h-3',
    };

    const textSizeClasses = {
        sm: 'text-xs',
        md: 'text-sm',
        lg: 'text-base',
    };

    const getStatusColor = () => {
        if (isConnected) return 'bg-green-500';
        if (isReconnecting) return 'bg-yellow-500';
        return 'bg-gray-400';
    };

    const getStatusText = () => {
        if (isConnected) return 'Connected';
        if (isReconnecting) return 'Reconnecting...';
        return 'Disconnected';
    };

    const getStatusTextColor = () => {
        if (isConnected) return 'text-green-500';
        if (isReconnecting) return 'text-yellow-500';
        return 'text-gray-400';
    };

    return (
        <div className={`flex items-center gap-2 ${className}`}>
            {/* Status indicator */}
            <div
                className={`
          ${sizeClasses[size]} 
          ${getStatusColor()} 
          rounded-full 
          ${isConnected ? 'animate-pulse shadow-lg shadow-green-500/50' : ''}
          ${isReconnecting ? 'animate-ping' : ''}
        `}
                title={getStatusText()}
            />

            {/* Label */}
            {showLabel && (
                <span className={`${textSizeClasses[size]} ${getStatusTextColor()} font-medium`}>
                    {getStatusText()}
                </span>
            )}

            {/* Reconnect button (only when disconnected) */}
            {!isConnected && !isReconnecting && onReconnect && (
                <button
                    onClick={onReconnect}
                    className={`
            ${textSizeClasses[size]}
            px-2 py-0.5
            text-blue-400 hover:text-blue-300
            hover:bg-blue-500/10
            rounded
            transition-colors
          `}
                    title="Click to reconnect"
                >
                    Reconnect
                </button>
            )}

            {/* Last connected time */}
            {!isConnected && lastConnected && (
                <span className="text-xs text-gray-500" title={lastConnected.toISOString()}>
                    (last: {formatTimeAgo(lastConnected)})
                </span>
            )}
        </div>
    );
}

/**
 * Format time ago string
 */
function formatTimeAgo(date: Date): string {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}
