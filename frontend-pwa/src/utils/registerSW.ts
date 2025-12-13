/**
 * Service Worker Registration
 * 
 * Registers the PWA service worker for offline support
 */

export function registerSW() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', async () => {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });

                console.log('[PWA] Service Worker registered:', registration.scope);

                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;

                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                // New version available
                                showUpdateNotification();
                            }
                        });
                    }
                });

                // Handle controller change (new SW activated)
                navigator.serviceWorker.addEventListener('controllerchange', () => {
                    console.log('[PWA] New Service Worker activated');
                });

            } catch (error) {
                console.error('[PWA] Service Worker registration failed:', error);
            }
        });
    }
}

/**
 * Show notification when new version is available
 */
function showUpdateNotification() {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('OpenEHRCore Atualizado', {
            body: 'Nova versão disponível. Recarregue a página.',
            icon: '/favicon.ico'
        });
    } else {
        // Fallback: create a toast/banner in the UI
        const banner = document.createElement('div');
        banner.id = 'sw-update-banner';
        banner.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #3b82f6;
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 9999;
                display: flex;
                gap: 16px;
                align-items: center;
            ">
                <span>Nova versão disponível!</span>
                <button onclick="window.location.reload()" style="
                    background: white;
                    color: #3b82f6;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                ">Atualizar</button>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 4px;
                    cursor: pointer;
                ">✕</button>
            </div>
        `;
        document.body.appendChild(banner);
    }
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
        console.log('[PWA] Notifications not supported');
        return false;
    }

    if (Notification.permission === 'granted') {
        return true;
    }

    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    return false;
}

/**
 * Check if app is installed as PWA
 */
export function isPWA(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true;
}

/**
 * Check if device is online
 */
export function isOnline(): boolean {
    return navigator.onLine;
}

/**
 * Add offline/online event listeners
 */
export function setupConnectivityListeners(
    onOnline?: () => void,
    onOffline?: () => void
) {
    window.addEventListener('online', () => {
        console.log('[PWA] Back online');
        onOnline?.();
    });

    window.addEventListener('offline', () => {
        console.log('[PWA] Gone offline');
        onOffline?.();
    });
}

// Auto-register on import
registerSW();
