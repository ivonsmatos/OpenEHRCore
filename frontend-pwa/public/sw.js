/**
 * OpenEHRCore Service Worker
 * 
 * Provides offline support for the PWA:
 * - Cache static assets
 * - Cache API responses
 * - Background sync for pending requests
 * - Push notifications support
 */

const CACHE_NAME = 'openehrcore-v1';
const STATIC_CACHE = 'openehrcore-static-v1';
const API_CACHE = 'openehrcore-api-v1';

// Assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/favicon.ico',
    '/src/main.tsx',
    '/src/App.tsx',
];

// API endpoints to cache
const CACHEABLE_API_ROUTES = [
    '/api/v1/patients',
    '/api/v1/practitioners',
    '/api/v1/organizations',
    '/api/v1/cbo/families',
    '/api/v1/cbo/doctors',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS).catch(err => {
                    console.warn('[SW] Some assets failed to cache:', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== STATIC_CACHE && name !== API_CACHE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip external requests
    if (!url.origin.includes(self.location.origin) &&
        !url.origin.includes('localhost:8000')) {
        return;
    }

    // API requests - Network first, then cache
    if (url.pathname.includes('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Static assets - Cache first, then network
    event.respondWith(cacheFirstStrategy(request));
});

/**
 * Cache First Strategy
 * For static assets - serve from cache, fall back to network
 */
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Refresh cache in background
        fetchAndCache(request);
        return cachedResponse;
    }

    return fetchAndCache(request);
}

/**
 * Network First Strategy
 * For API requests - try network, fall back to cache
 */
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful API responses
        if (networkResponse.ok && shouldCacheApiResponse(request.url)) {
            const cache = await caches.open(API_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);

        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline fallback for API
        return new Response(
            JSON.stringify({
                error: 'Offline',
                message: 'Você está offline. Os dados mostrados podem estar desatualizados.',
                cached: true
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

/**
 * Fetch and cache response
 */
async function fetchAndCache(request) {
    try {
        const response = await fetch(request);

        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', error);
        throw error;
    }
}

/**
 * Check if API response should be cached
 */
function shouldCacheApiResponse(url) {
    return CACHEABLE_API_ROUTES.some(route => url.includes(route));
}

// Background Sync - for pending mutations
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === 'sync-pending-requests') {
        event.waitUntil(syncPendingRequests());
    }
});

/**
 * Sync pending requests when back online
 */
async function syncPendingRequests() {
    try {
        // Get pending requests from IndexedDB
        const db = await openDB();
        const pending = await getAllPending(db);

        for (const item of pending) {
            try {
                await fetch(item.url, {
                    method: item.method,
                    headers: item.headers,
                    body: item.body
                });

                // Remove from pending
                await removePending(db, item.id);
                console.log('[SW] Synced request:', item.url);
            } catch (error) {
                console.error('[SW] Failed to sync:', item.url);
            }
        }
    } catch (error) {
        console.error('[SW] Sync failed:', error);
    }
}

// IndexedDB helpers for offline queue
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('openehrcore-offline', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending')) {
                db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

function getAllPending(db) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending', 'readonly');
        const store = tx.objectStore('pending');
        const request = store.getAll();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function removePending(db, id) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending', 'readwrite');
        const store = tx.objectStore('pending');
        const request = store.delete(id);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

// Push notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    let data = { title: 'OpenEHRCore', body: 'Nova notificação' };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        vibrate: [100, 50, 100],
        data: data.url || '/',
        actions: [
            { action: 'open', title: 'Abrir' },
            { action: 'close', title: 'Fechar' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.openWindow(event.notification.data || '/')
        );
    }
});

console.log('[SW] Service Worker loaded');
