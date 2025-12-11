/**
 * Sprint 25: Frontend Performance Utilities
 * 
 * Utilities for:
 * - Debouncing and throttling
 * - Memoization
 * - Virtual scrolling helpers
 * - Image optimization
 * - Performance monitoring
 */

import React from 'react';

/**
 * Debounce a function call.
 * Delays execution until after wait milliseconds have elapsed since last call.
 */
export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    return function (this: any, ...args: Parameters<T>) {
        if (timeoutId !== null) {
            clearTimeout(timeoutId);
        }

        timeoutId = setTimeout(() => {
            func.apply(this, args);
            timeoutId = null;
        }, wait);
    };
}

/**
 * Throttle a function call.
 * Ensures function is called at most once per wait milliseconds.
 */
export function throttle<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let lastTime = 0;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    return function (this: any, ...args: Parameters<T>) {
        const now = Date.now();
        const remaining = wait - (now - lastTime);

        if (remaining <= 0) {
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            lastTime = now;
            func.apply(this, args);
        } else if (timeoutId === null) {
            timeoutId = setTimeout(() => {
                lastTime = Date.now();
                timeoutId = null;
                func.apply(this, args);
            }, remaining);
        }
    };
}

/**
 * Memoize a function with a single argument.
 */
export function memoize<T, R>(
    func: (arg: T) => R,
    options?: { maxSize?: number }
): (arg: T) => R {
    const cache = new Map<T, R>();
    const maxSize = options?.maxSize ?? 100;

    return (arg: T) => {
        if (cache.has(arg)) {
            return cache.get(arg)!;
        }

        const result = func(arg);

        // Evict oldest entry if at max size
        if (cache.size >= maxSize) {
            const firstKey = cache.keys().next().value;
            if (firstKey !== undefined) {
                cache.delete(firstKey);
            }
        }

        cache.set(arg, result);
        return result;
    };
}

/**
 * Create an intersection observer for lazy loading.
 */
export function createLazyObserver(
    callback: (entries: IntersectionObserverEntry[]) => void,
    options?: IntersectionObserverInit
): IntersectionObserver | null {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
        return null;
    }

    return new IntersectionObserver(callback, {
        root: null,
        rootMargin: '50px',
        threshold: 0.1,
        ...options
    });
}

/**
 * Request idle callback with fallback for unsupported browsers.
 */
export function requestIdleCallback(
    callback: () => void,
    options?: { timeout?: number }
): number {
    if ('requestIdleCallback' in window) {
        return (window as any).requestIdleCallback(callback, options);
    }
    return setTimeout(callback, 1) as unknown as number;
}

/**
 * Cancel idle callback with fallback.
 */
export function cancelIdleCallback(id: number): void {
    if ('cancelIdleCallback' in window) {
        (window as any).cancelIdleCallback(id);
    } else {
        clearTimeout(id);
    }
}

/**
 * Prefetch a route/component for faster navigation.
 */
export function prefetchRoute(importFn: () => Promise<any>): void {
    requestIdleCallback(() => {
        importFn().catch(() => {
            // Silently ignore prefetch errors
        });
    });
}

/**
 * Image lazy loading helper.
 * Returns a placeholder until image is in viewport.
 */
export function getImageUrl(
    src: string,
    _options?: {
        width?: number;
        quality?: number;
        placeholder?: string;
    }
): string {
    // If using a CDN with image optimization, construct URL here
    // For now, just return the source
    return src;
}

/**
 * Performance measurement utility.
 */
export class PerformanceMonitor {
    private static marks: Map<string, number> = new Map();
    private static measures: Map<string, number[]> = new Map();

    /**
     * Start a performance measurement.
     */
    static start(label: string): void {
        this.marks.set(label, performance.now());
    }

    /**
     * End a performance measurement and log the result.
     */
    static end(label: string): number {
        const startTime = this.marks.get(label);
        if (startTime === undefined) {
            console.warn(`No start mark found for "${label}"`);
            return 0;
        }

        const duration = performance.now() - startTime;
        this.marks.delete(label);

        // Store measure for averaging
        if (!this.measures.has(label)) {
            this.measures.set(label, []);
        }
        this.measures.get(label)!.push(duration);

        if (process.env.NODE_ENV === 'development') {
            console.log(`[Perf] ${label}: ${duration.toFixed(2)}ms`);
        }

        return duration;
    }

    /**
     * Get average duration for a label.
     */
    static getAverage(label: string): number {
        const measures = this.measures.get(label);
        if (!measures || measures.length === 0) return 0;
        return measures.reduce((a, b) => a + b, 0) / measures.length;
    }

    /**
     * Get all performance data.
     */
    static getReport(): Record<string, { count: number; avg: number; total: number }> {
        const report: Record<string, { count: number; avg: number; total: number }> = {};

        this.measures.forEach((measures, label) => {
            const total = measures.reduce((a, b) => a + b, 0);
            report[label] = {
                count: measures.length,
                avg: Math.round(total / measures.length),
                total: Math.round(total)
            };
        });

        return report;
    }

    /**
     * Clear all measurements.
     */
    static clear(): void {
        this.marks.clear();
        this.measures.clear();
    }
}

/**
 * Chunk an array for batch processing.
 */
export function chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += chunkSize) {
        chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
}

/**
 * Process items in batches with delay between batches.
 * Useful for rendering large lists without blocking UI.
 */
export async function processBatched<T, R>(
    items: T[],
    processor: (item: T) => R,
    options?: { batchSize?: number; delayMs?: number }
): Promise<R[]> {
    const batchSize = options?.batchSize ?? 50;
    const delayMs = options?.delayMs ?? 0;
    const results: R[] = [];

    const chunks = chunkArray(items, batchSize);

    for (const chunk of chunks) {
        const batchResults = chunk.map(processor);
        results.push(...batchResults);

        if (delayMs > 0) {
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }

    return results;
}

/**
 * Virtual list helper - calculates visible items.
 */
export function getVisibleItems<T>(
    items: T[],
    scrollTop: number,
    viewportHeight: number,
    itemHeight: number,
    overscan: number = 5
): { startIndex: number; endIndex: number; visibleItems: T[]; offsetTop: number } {
    const totalItems = items.length;

    let startIndex = Math.floor(scrollTop / itemHeight) - overscan;
    startIndex = Math.max(0, startIndex);

    let endIndex = Math.ceil((scrollTop + viewportHeight) / itemHeight) + overscan;
    endIndex = Math.min(totalItems - 1, endIndex);

    const visibleItems = items.slice(startIndex, endIndex + 1);
    const offsetTop = startIndex * itemHeight;

    return { startIndex, endIndex, visibleItems, offsetTop };
}

/**
 * React hook for detecting if component is in viewport.
 */
export function useInViewport(
    ref: React.RefObject<HTMLElement>,
    options?: IntersectionObserverInit
): boolean {
    const [isInViewport, setIsInViewport] = React.useState(false);

    React.useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const observer = createLazyObserver(
            (entries) => {
                entries.forEach(entry => {
                    setIsInViewport(entry.isIntersecting);
                });
            },
            options
        );

        if (observer) {
            observer.observe(element);
            return () => observer.disconnect();
        }
    }, [ref, options]);

    return isInViewport;
}


/**
 * Hook for debounced value.
 */
export function useDebouncedValue<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = React.useState(value);

    React.useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);

    return debouncedValue;
}

/**
 * Hook for throttled callback.
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
    callback: T,
    delay: number
): T {
    const throttledFn = React.useMemo(
        () => throttle(callback, delay),
        [callback, delay]
    );

    return throttledFn as T;
}
