/**
 * React hook for visual alerts (browser notifications, sound, tab badge).
 * Provides controls for enabling/disabling various alert types.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface VisualAlertSettings {
    browserNotifications: boolean;
    soundEnabled: boolean;
    tabBadge: boolean;
    navbarFlash: boolean;
}

interface UseVisualAlertsReturn {
    settings: VisualAlertSettings;
    notificationPermission: NotificationPermission | 'unsupported';
    isNavbarFlashing: boolean;
    requestNotificationPermission: () => Promise<boolean>;
    toggleBrowserNotifications: () => void;
    toggleSound: () => void;
    toggleTabBadge: () => void;
    toggleNavbarFlash: () => void;
    triggerAlert: (options: {
        title: string;
        message: string;
        severity?: 'info' | 'warning' | 'error' | 'critical';
        playSound?: boolean;
    }) => void;
    clearNavbarFlash: () => void;
}

const STORAGE_KEY = 'elk-vision-alert-settings';

const DEFAULT_SETTINGS: VisualAlertSettings = {
    browserNotifications: true,
    soundEnabled: false,
    tabBadge: true,
    navbarFlash: true,
};

/**
 * Hook for managing visual alerts and browser notifications.
 */
export function useVisualAlerts(): UseVisualAlertsReturn {
    const [settings, setSettings] = useState<VisualAlertSettings>(DEFAULT_SETTINGS);
    const [notificationPermission, setNotificationPermission] = useState<NotificationPermission | 'unsupported'>('default');
    const [isNavbarFlashing, setIsNavbarFlashing] = useState(false);

    const audioRef = useRef<HTMLAudioElement | null>(null);
    const originalFaviconRef = useRef<string>('');
    const badgeCountRef = useRef<number>(0);

    // Load settings from localStorage
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setSettings({ ...DEFAULT_SETTINGS, ...parsed });
            } catch (e) {
                console.error('Failed to parse alert settings:', e);
            }
        }

        // Check notification permission
        if ('Notification' in window) {
            setNotificationPermission(Notification.permission);
        } else {
            setNotificationPermission('unsupported');
        }

        // Store original favicon
        const faviconLink = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
        if (faviconLink) {
            originalFaviconRef.current = faviconLink.href;
        }

        // Create audio element
        audioRef.current = new Audio('/sounds/alert.mp3');
        audioRef.current.volume = 0.5;

        return () => {
            // Restore original favicon on unmount
            if (originalFaviconRef.current) {
                updateFavicon(originalFaviconRef.current);
            }
        };
    }, []);

    // Save settings to localStorage when they change
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
        }
    }, [settings]);

    const requestNotificationPermission = useCallback(async (): Promise<boolean> => {
        if (!('Notification' in window)) {
            setNotificationPermission('unsupported');
            return false;
        }

        if (Notification.permission === 'granted') {
            setNotificationPermission('granted');
            return true;
        }

        if (Notification.permission === 'denied') {
            setNotificationPermission('denied');
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            setNotificationPermission(permission);
            return permission === 'granted';
        } catch (e) {
            console.error('Failed to request notification permission:', e);
            return false;
        }
    }, []);

    const toggleBrowserNotifications = useCallback(() => {
        setSettings(prev => ({
            ...prev,
            browserNotifications: !prev.browserNotifications,
        }));
    }, []);

    const toggleSound = useCallback(() => {
        setSettings(prev => ({
            ...prev,
            soundEnabled: !prev.soundEnabled,
        }));
    }, []);

    const toggleTabBadge = useCallback(() => {
        setSettings(prev => ({
            ...prev,
            tabBadge: !prev.tabBadge,
        }));
    }, []);

    const toggleNavbarFlash = useCallback(() => {
        setSettings(prev => ({
            ...prev,
            navbarFlash: !prev.navbarFlash,
        }));
    }, []);

    const updateFavicon = useCallback((href: string) => {
        let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
        if (!link) {
            link = document.createElement('link');
            link.rel = 'icon';
            document.head.appendChild(link);
        }
        link.href = href;
    }, []);

    const createBadgeFavicon = useCallback((count: number): string => {
        // Create a canvas to draw badge on favicon
        const canvas = document.createElement('canvas');
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');
        if (!ctx) return originalFaviconRef.current;

        // Draw red circle background
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(16, 16, 14, 0, Math.PI * 2);
        ctx.fill();

        // Draw count text
        ctx.fillStyle = 'white';
        ctx.font = 'bold 18px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const displayCount = count > 99 ? '99+' : count.toString();
        ctx.fillText(displayCount, 16, 17);

        return canvas.toDataURL('image/png');
    }, []);

    const triggerAlert = useCallback(({
        title,
        message,
        severity = 'error',
        playSound = true,
    }: {
        title: string;
        message: string;
        severity?: 'info' | 'warning' | 'error' | 'critical';
        playSound?: boolean;
    }) => {
        const shouldAlert = severity === 'error' || severity === 'critical';

        // Browser notification
        if (settings.browserNotifications && shouldAlert && notificationPermission === 'granted') {
            try {
                const notification = new Notification(title, {
                    body: message,
                    icon: '/favicon.ico',
                    tag: 'elk-vision-alert',
                    requireInteraction: severity === 'critical',
                });

                notification.onclick = () => {
                    window.focus();
                    notification.close();
                };

                // Auto-close after 10 seconds (unless critical)
                if (severity !== 'critical') {
                    setTimeout(() => notification.close(), 10000);
                }
            } catch (e) {
                console.error('Failed to show notification:', e);
            }
        }

        // Sound alert
        if (settings.soundEnabled && playSound && shouldAlert && audioRef.current) {
            audioRef.current.currentTime = 0;
            audioRef.current.play().catch(e => {
                console.error('Failed to play alert sound:', e);
            });
        }

        // Tab badge
        if (settings.tabBadge && shouldAlert) {
            badgeCountRef.current += 1;
            const badgeFavicon = createBadgeFavicon(badgeCountRef.current);
            updateFavicon(badgeFavicon);

            // Update document title with count
            const baseTitle = document.title.replace(/^\(\d+\+?\)\s*/, '');
            document.title = `(${badgeCountRef.current}) ${baseTitle}`;
        }

        // Navbar flash
        if (settings.navbarFlash && shouldAlert) {
            setIsNavbarFlashing(true);

            // Auto-clear after 3 seconds
            setTimeout(() => {
                setIsNavbarFlashing(false);
            }, 3000);
        }
    }, [settings, notificationPermission, createBadgeFavicon, updateFavicon]);

    const clearNavbarFlash = useCallback(() => {
        setIsNavbarFlashing(false);

        // Also clear badge
        badgeCountRef.current = 0;
        if (originalFaviconRef.current) {
            updateFavicon(originalFaviconRef.current);
        }

        // Reset title
        const baseTitle = document.title.replace(/^\(\d+\+?\)\s*/, '');
        document.title = baseTitle;
    }, [updateFavicon]);

    return {
        settings,
        notificationPermission,
        isNavbarFlashing,
        requestNotificationPermission,
        toggleBrowserNotifications,
        toggleSound,
        toggleTabBadge,
        toggleNavbarFlash,
        triggerAlert,
        clearNavbarFlash,
    };
}
