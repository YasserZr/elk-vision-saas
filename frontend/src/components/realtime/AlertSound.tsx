/**
 * Alert Sound Component
 * 
 * Provides controls for alert sound:
 * - Toggle button for enabling/disabling
 * - Visual indicator of current state
 * - Preloads audio for instant playback
 */

'use client';

import React from 'react';

interface AlertSoundProps {
    enabled: boolean;
    onToggle: () => void;
    className?: string;
}

export default function AlertSound({ enabled, onToggle, className = '' }: AlertSoundProps) {
    return (
        <button
            onClick={onToggle}
            className={`
        flex items-center gap-2 px-3 py-1.5 rounded-lg
        transition-colors duration-200
        ${enabled
                    ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30'
                    : 'bg-gray-700/50 text-gray-500 hover:bg-gray-700 hover:text-gray-400'
                }
        ${className}
      `}
            title={enabled ? 'Sound alerts enabled' : 'Sound alerts disabled'}
        >
            {enabled ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                    />
                </svg>
            ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                    />
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                    />
                </svg>
            )}
            <span className="text-xs font-medium">
                {enabled ? 'Sound On' : 'Sound Off'}
            </span>
        </button>
    );
}
