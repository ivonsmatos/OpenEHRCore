const CACHE_NAME = 'healthstack-v2.0.1';
const OFFLINE_URL = '/offline.html';

// Static assets to cache - only files that exist
const STATIC_ASSETS = [
    '/',
    '/offline.html',
    '/manifest.json',
];

// API endpoints to cache for offline
const API_CACHE_PATTERNS = [
    /\/api\/v1\/patients\/?$/,
    /\/api\/v1\/practitioners\/?$/,
    /\/api\/v1\/organizations\/?$/,
    /\/api\/v1\/locations\/?$/,
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(async (cache) => {
                console.log('[SW] Caching static assets');
                // Cache each asset individually to handle errors gracefully
                for (const url of STATIC_ASSETS) {
                    try {
                        await cache.add(url);
                    } catch (err) {
                        console.warn('[SW] Failed to cache:', url, err);
                    }
                }
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        // Queue POST/PUT/DELETE for sync when offline
        if (!navigator.onLine) {
            event.respondWith(handleOfflineRequest(request));
        }
        return;
    }

    // API requests - Network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Static assets - Cache first, network fallback
    event.respondWith(cacheFirstStrategy(request));
});

// Network first strategy (for API calls)
async function networkFirstStrategy(request) {
    try {
        const response = await fetch(request);

        // Cache successful GET responses
        if (response.ok && shouldCacheAPI(request.url)) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // Network failed, try cache
        const cached = await caches.match(request);
        if (cached) {
            console.log('[SW] Serving from cache:', request.url);
            return cached;
        }

        // Return offline response for API
        return new Response(
            JSON.stringify({
                error: 'offline',
                message: 'You are offline. Data will sync when connection is restored.',
                cached: false
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Cache first strategy (for static assets)
async function cacheFirstStrategy(request) {
    const cached = await caches.match(request);

    if (cached) {
        // Return cached, but also fetch in background to update
        fetchAndCache(request);
        return cached;
    }

    try {
        const response = await fetch(request);

        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
        }
        throw error;
    }
}

// Background fetch and cache update
async function fetchAndCache(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
    } catch (error) {
        // Ignore background update errors
    }
}

// Check if API response should be cached
function shouldCacheAPI(url) {
    return API_CACHE_PATTERNS.some(pattern => pattern.test(url));
}

// Handle offline POST/PUT/DELETE requests
async function handleOfflineRequest(request) {
    // Queue request for later sync
    const requestData = {
        url: request.url,
        method: request.method,
        headers: Object.fromEntries(request.headers.entries()),
        body: await request.clone().text(),
        timestamp: Date.now()
    };

    // Store in IndexedDB for later sync
    await storeOfflineRequest(requestData);

    return new Response(
        JSON.stringify({
            status: 'queued',
            message: 'Request queued for sync when online',
            offline: true
        }),
        {
            status: 202,
            headers: { 'Content-Type': 'application/json' }
        }
    );
}

// Store offline request in IndexedDB
async function storeOfflineRequest(requestData) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('healthstack-offline', 1);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending-requests')) {
                db.createObjectStore('pending-requests', { keyPath: 'timestamp' });
            }
        };

        request.onsuccess = (event) => {
            const db = event.target.result;
            const tx = db.transaction('pending-requests', 'readwrite');
            const store = tx.objectStore('pending-requests');
            store.add(requestData);
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        };

        request.onerror = () => reject(request.error);
    });
}

// Background sync - process queued requests
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-pending-requests') {
        event.waitUntil(syncPendingRequests());
    }
});

// Sync all pending requests
async function syncPendingRequests() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('healthstack-offline', 1);

        request.onsuccess = async (event) => {
            const db = event.target.result;
            const tx = db.transaction('pending-requests', 'readwrite');
            const store = tx.objectStore('pending-requests');
            const allRequests = store.getAll();

            allRequests.onsuccess = async () => {
                const requests = allRequests.result;

                for (const reqData of requests) {
                    try {
                        await fetch(reqData.url, {
                            method: reqData.method,
                            headers: reqData.headers,
                            body: reqData.body
                        });

                        // Remove successful request from queue
                        store.delete(reqData.timestamp);
                        console.log('[SW] Synced request:', reqData.url);
                    } catch (error) {
                        console.error('[SW] Sync failed:', reqData.url, error);
                    }
                }

                resolve();
            };
        };

        request.onerror = () => reject(request.error);
    });
}

// Listen for online event to trigger sync
self.addEventListener('message', (event) => {
    if (event.data === 'ONLINE') {
        console.log('[SW] Online - triggering sync');
        syncPendingRequests();
    }
});

console.log('[SW] HealthStack Service Worker loaded');
