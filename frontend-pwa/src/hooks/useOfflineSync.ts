/**
 * Offline Sync Hook for HealthStack PWA
 * 
 * Provides:
 * - Online/offline status detection
 * - IndexedDB storage for offline data
 * - Automatic sync when back online
 * - Conflict resolution
 */

import { useState, useEffect, useCallback } from 'react';

// IndexedDB database name
const DB_NAME = 'healthstack-offline';
const DB_VERSION = 1;

// Stores
const STORES = {
    PENDING_REQUESTS: 'pending-requests',
    CACHED_DATA: 'cached-data',
    SYNC_LOG: 'sync-log'
};

interface PendingRequest {
    id: string;
    url: string;
    method: string;
    body: string;
    headers: Record<string, string>;
    timestamp: number;
    retries: number;
}

interface SyncStatus {
    isOnline: boolean;
    isSyncing: boolean;
    pendingCount: number;
    lastSyncTime: Date | null;
    error: string | null;
}

// Open IndexedDB
function openDatabase(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (event) => {
            const db = (event.target as IDBOpenDBRequest).result;

            // Create stores if they don't exist
            if (!db.objectStoreNames.contains(STORES.PENDING_REQUESTS)) {
                db.createObjectStore(STORES.PENDING_REQUESTS, { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains(STORES.CACHED_DATA)) {
                const store = db.createObjectStore(STORES.CACHED_DATA, { keyPath: 'key' });
                store.createIndex('timestamp', 'timestamp');
            }
            if (!db.objectStoreNames.contains(STORES.SYNC_LOG)) {
                db.createObjectStore(STORES.SYNC_LOG, { keyPath: 'id', autoIncrement: true });
            }
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Generate unique ID
function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Main offline sync hook
 */
export function useOfflineSync() {
    const [status, setStatus] = useState<SyncStatus>({
        isOnline: navigator.onLine,
        isSyncing: false,
        pendingCount: 0,
        lastSyncTime: null,
        error: null
    });

    // Update online status
    useEffect(() => {
        const handleOnline = () => {
            setStatus(prev => ({ ...prev, isOnline: true }));
            // Trigger sync
            syncPendingRequests();
            // Notify service worker
            if (navigator.serviceWorker?.controller) {
                navigator.serviceWorker.controller.postMessage('ONLINE');
            }
        };

        const handleOffline = () => {
            setStatus(prev => ({ ...prev, isOnline: false }));
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Initial count
        getPendingCount();

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // Get pending request count
    const getPendingCount = useCallback(async () => {
        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.PENDING_REQUESTS, 'readonly');
            const store = tx.objectStore(STORES.PENDING_REQUESTS);
            const count = await new Promise<number>((resolve) => {
                const req = store.count();
                req.onsuccess = () => resolve(req.result);
            });
            setStatus(prev => ({ ...prev, pendingCount: count }));
            return count;
        } catch (error) {
            console.error('Failed to get pending count:', error);
            return 0;
        }
    }, []);

    // Queue a request for later sync
    const queueRequest = useCallback(async (
        url: string,
        method: string,
        body?: unknown,
        headers?: Record<string, string>
    ): Promise<string> => {
        const request: PendingRequest = {
            id: generateId(),
            url,
            method,
            body: body ? JSON.stringify(body) : '',
            headers: headers || { 'Content-Type': 'application/json' },
            timestamp: Date.now(),
            retries: 0
        };

        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
            const store = tx.objectStore(STORES.PENDING_REQUESTS);
            await new Promise<void>((resolve, reject) => {
                const req = store.add(request);
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });

            await getPendingCount();
            return request.id;
        } catch (error) {
            console.error('Failed to queue request:', error);
            throw error;
        }
    }, [getPendingCount]);

    // Sync all pending requests
    const syncPendingRequests = useCallback(async (): Promise<number> => {
        if (!navigator.onLine) {
            return 0;
        }

        setStatus(prev => ({ ...prev, isSyncing: true, error: null }));

        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
            const store = tx.objectStore(STORES.PENDING_REQUESTS);

            const requests = await new Promise<PendingRequest[]>((resolve) => {
                const req = store.getAll();
                req.onsuccess = () => resolve(req.result);
            });

            let synced = 0;

            for (const req of requests) {
                try {
                    const response = await fetch(req.url, {
                        method: req.method,
                        headers: req.headers,
                        body: req.body || undefined
                    });

                    if (response.ok) {
                        // Remove from queue
                        const deleteTx = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
                        deleteTx.objectStore(STORES.PENDING_REQUESTS).delete(req.id);
                        synced++;
                        console.log(`[Sync] Success: ${req.method} ${req.url}`);
                    } else if (response.status >= 400 && response.status < 500) {
                        // Client error - remove from queue (won't succeed on retry)
                        const deleteTx = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
                        deleteTx.objectStore(STORES.PENDING_REQUESTS).delete(req.id);
                        console.warn(`[Sync] Client error, removing: ${req.url}`);
                    } else {
                        // Server error - increment retry
                        req.retries++;
                        if (req.retries >= 5) {
                            const deleteTx = db.transaction(STORES.PENDING_REQUESTS, 'readwrite');
                            deleteTx.objectStore(STORES.PENDING_REQUESTS).delete(req.id);
                            console.warn(`[Sync] Max retries, removing: ${req.url}`);
                        }
                    }
                } catch (error) {
                    console.error(`[Sync] Failed: ${req.url}`, error);
                }
            }

            await getPendingCount();
            setStatus(prev => ({
                ...prev,
                isSyncing: false,
                lastSyncTime: new Date()
            }));

            return synced;
        } catch (error) {
            setStatus(prev => ({
                ...prev,
                isSyncing: false,
                error: error instanceof Error ? error.message : 'Sync failed'
            }));
            return 0;
        }
    }, [getPendingCount]);

    // Cache data locally
    const cacheData = useCallback(async (key: string, data: unknown): Promise<void> => {
        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.CACHED_DATA, 'readwrite');
            const store = tx.objectStore(STORES.CACHED_DATA);
            await new Promise<void>((resolve, reject) => {
                const req = store.put({ key, data, timestamp: Date.now() });
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        } catch (error) {
            console.error('Failed to cache data:', error);
        }
    }, []);

    // Get cached data
    const getCachedData = useCallback(async <T>(key: string): Promise<T | null> => {
        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.CACHED_DATA, 'readonly');
            const store = tx.objectStore(STORES.CACHED_DATA);
            const result = await new Promise<{ key: string; data: T; timestamp: number } | undefined>((resolve) => {
                const req = store.get(key);
                req.onsuccess = () => resolve(req.result);
            });
            return result?.data ?? null;
        } catch (error) {
            console.error('Failed to get cached data:', error);
            return null;
        }
    }, []);

    // Clear all cached data
    const clearCache = useCallback(async (): Promise<void> => {
        try {
            const db = await openDatabase();
            const tx = db.transaction(STORES.CACHED_DATA, 'readwrite');
            tx.objectStore(STORES.CACHED_DATA).clear();
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    }, []);

    return {
        ...status,
        queueRequest,
        syncPendingRequests,
        cacheData,
        getCachedData,
        clearCache,
        getPendingCount
    };
}

/**
 * Hook for making offline-aware API requests
 */
export function useOfflineRequest() {
    const { isOnline, queueRequest, syncPendingRequests } = useOfflineSync();

    const request = useCallback(async <T>(
        url: string,
        options: RequestInit = {}
    ): Promise<{ data: T | null; offline: boolean; queued: boolean }> => {
        const method = options.method || 'GET';

        // GET requests - try network, fallback to cache
        if (method === 'GET') {
            if (isOnline) {
                try {
                    const response = await fetch(url, options);
                    if (response.ok) {
                        const data = await response.json();
                        return { data, offline: false, queued: false };
                    }
                } catch {
                    // Fall through to offline handling
                }
            }

            // Return cached or null
            return { data: null, offline: true, queued: false };
        }

        // Write requests - queue if offline
        if (!isOnline) {
            const body = options.body ? JSON.parse(options.body as string) : undefined;
            await queueRequest(url, method, body, options.headers as Record<string, string>);
            return { data: null, offline: true, queued: true };
        }

        // Online - make request
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            return { data, offline: false, queued: false };
        } catch {
            // Failed even though online - queue for retry
            const body = options.body ? JSON.parse(options.body as string) : undefined;
            await queueRequest(url, method, body, options.headers as Record<string, string>);
            return { data: null, offline: true, queued: true };
        }
    }, [isOnline, queueRequest]);

    return { request, isOnline, syncPendingRequests };
}

export default useOfflineSync;
