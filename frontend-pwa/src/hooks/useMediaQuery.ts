import { useState, useEffect } from 'react';

export const breakpoints = {
    mobile: 768,
    tablet: 1024,
    desktop: 1280
};

export const mediaQueries = {
    mobile: `(max-width: ${breakpoints.mobile - 1}px)`,
    tablet: `(min-width: ${breakpoints.mobile}px) and (max-width: ${breakpoints.tablet - 1}px)`,
    desktop: `(min-width: ${breakpoints.tablet}px)`,
    tabletAndBelow: `(max-width: ${breakpoints.tablet - 1}px)`,
    mobileAndBelow: `(max-width: ${breakpoints.mobile - 1}px)`
};

/**
 * Hook para detectar media queries e tornar componentes responsivos
 * 
 * @param query - Media query string (ex: '(max-width: 768px)')
 * @returns boolean indicando se a media query corresponde
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState<boolean>(() => {
        if (typeof window !== 'undefined') {
            return window.matchMedia(query).matches;
        }
        return false;
    });

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const mediaQueryList = window.matchMedia(query);
        const handleChange = (event: MediaQueryListEvent) => {
            setMatches(event.matches);
        };

        // Set initial value
        setMatches(mediaQueryList.matches);

        // Modern browsers
        if (mediaQueryList.addEventListener) {
            mediaQueryList.addEventListener('change', handleChange);
            return () => mediaQueryList.removeEventListener('change', handleChange);
        }
        // Fallback for older browsers
        else {
            mediaQueryList.addListener(handleChange);
            return () => mediaQueryList.removeListener(handleChange);
        }
    }, [query]);

    return matches;
}

/**
 * Hook específico para detectar dispositivos mobile
 */
export function useIsMobile(): boolean {
    return useMediaQuery(mediaQueries.mobileAndBelow);
}

/**
 * Hook específico para detectar tablets e mobile
 */
export function useIsTabletOrBelow(): boolean {
    return useMediaQuery(mediaQueries.tabletAndBelow);
}

/**
 * Hook que retorna o tipo de dispositivo atual
 */
export function useDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    const isMobile = useMediaQuery(mediaQueries.mobile);
    const isTablet = useMediaQuery(mediaQueries.tablet);
    
    if (isMobile) return 'mobile';
    if (isTablet) return 'tablet';
    return 'desktop';
}
