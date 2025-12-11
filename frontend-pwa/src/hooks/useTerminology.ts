/**
 * Sprint 21: Terminology Hook
 * 
 * React hook for terminology operations with caching and debounced search.
 */

import { useState, useCallback, useEffect } from 'react';
import { useDebounce } from './useDebounce';
import terminologyApi, {
    RxNormResult,
    ICD10Result,
    TUSSResult,
    TUSSType,
    MultiDrugInteraction
} from '../services/terminologyApi';

// ============================================================================
// useRxNormSearch Hook
// ============================================================================

interface UseRxNormSearchResult {
    results: RxNormResult[];
    loading: boolean;
    error: string | null;
    search: (query: string) => void;
}

export function useRxNormSearch(debounceMs: number = 300): UseRxNormSearchResult {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<RxNormResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const debouncedQuery = useDebounce(query, debounceMs);

    useEffect(() => {
        if (!debouncedQuery || debouncedQuery.length < 2) {
            setResults([]);
            return;
        }

        let cancelled = false;
        setLoading(true);
        setError(null);

        terminologyApi.searchRxNorm(debouncedQuery)
            .then((data) => {
                if (!cancelled) {
                    setResults(data);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setError(err.message || 'Erro ao buscar medicamentos');
                    setResults([]);
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [debouncedQuery]);

    const search = useCallback((q: string) => {
        setQuery(q);
    }, []);

    return { results, loading, error, search };
}

// ============================================================================
// useDrugInteractions Hook
// ============================================================================

interface UseDrugInteractionsResult {
    interactions: MultiDrugInteraction[];
    hasInteractions: boolean;
    loading: boolean;
    error: string | null;
    checkInteractions: (rxcuis: string[]) => Promise<void>;
}

export function useDrugInteractions(): UseDrugInteractionsResult {
    const [interactions, setInteractions] = useState<MultiDrugInteraction[]>([]);
    const [hasInteractions, setHasInteractions] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const checkInteractions = useCallback(async (rxcuis: string[]) => {
        if (rxcuis.length < 2) {
            setInteractions([]);
            setHasInteractions(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await terminologyApi.checkMultiDrugInteractions(rxcuis);
            setInteractions(result.interactions);
            setHasInteractions(result.hasInteractions);
        } catch (err: any) {
            setError(err.message || 'Erro ao verificar interações');
            setInteractions([]);
            setHasInteractions(false);
        } finally {
            setLoading(false);
        }
    }, []);

    return { interactions, hasInteractions, loading, error, checkInteractions };
}

// ============================================================================
// useICD10Search Hook
// ============================================================================

interface UseICD10SearchResult {
    results: ICD10Result[];
    loading: boolean;
    error: string | null;
    search: (query: string) => void;
}

export function useICD10Search(debounceMs: number = 300): UseICD10SearchResult {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<ICD10Result[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const debouncedQuery = useDebounce(query, debounceMs);

    useEffect(() => {
        if (!debouncedQuery || debouncedQuery.length < 2) {
            setResults([]);
            return;
        }

        let cancelled = false;
        setLoading(true);
        setError(null);

        terminologyApi.searchICD10(debouncedQuery)
            .then((data) => {
                if (!cancelled) {
                    setResults(data);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setError(err.message || 'Erro ao buscar códigos CID-10');
                    setResults([]);
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [debouncedQuery]);

    const search = useCallback((q: string) => {
        setQuery(q);
    }, []);

    return { results, loading, error, search };
}

// ============================================================================
// useTUSSSearch Hook
// ============================================================================

interface UseTUSSSearchResult {
    results: TUSSResult[];
    loading: boolean;
    error: string | null;
    search: (query: string, type?: TUSSType) => void;
}

export function useTUSSSearch(debounceMs: number = 300): UseTUSSSearchResult {
    const [query, setQuery] = useState('');
    const [typeFilter, setTypeFilter] = useState<TUSSType | undefined>();
    const [results, setResults] = useState<TUSSResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const debouncedQuery = useDebounce(query, debounceMs);

    useEffect(() => {
        if (!debouncedQuery || debouncedQuery.length < 2) {
            setResults([]);
            return;
        }

        let cancelled = false;
        setLoading(true);
        setError(null);

        terminologyApi.searchTUSS(debouncedQuery, typeFilter)
            .then((data) => {
                if (!cancelled) {
                    setResults(data);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setError(err.message || 'Erro ao buscar códigos TUSS');
                    setResults([]);
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [debouncedQuery, typeFilter]);

    const search = useCallback((q: string, type?: TUSSType) => {
        setQuery(q);
        setTypeFilter(type);
    }, []);

    return { results, loading, error, search };
}

// ============================================================================
// useTerminologyMapping Hook
// ============================================================================

interface UseTerminologyMappingResult {
    mappedCode: string | null;
    mappedDisplay: string | null;
    equivalence: string | null;
    loading: boolean;
    error: string | null;
    mapICD10ToSNOMED: (icd10Code: string) => Promise<void>;
    mapSNOMEDToICD10: (snomedCode: string) => Promise<void>;
}

export function useTerminologyMapping(): UseTerminologyMappingResult {
    const [mappedCode, setMappedCode] = useState<string | null>(null);
    const [mappedDisplay, setMappedDisplay] = useState<string | null>(null);
    const [equivalence, setEquivalence] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const mapICD10ToSNOMED = useCallback(async (icd10Code: string) => {
        setLoading(true);
        setError(null);

        try {
            const result = await terminologyApi.mapICD10ToSNOMED(icd10Code);
            if (result.mapped) {
                setMappedCode(result.target_code || null);
                setMappedDisplay(result.target_display || null);
                setEquivalence(result.equivalence || null);
            } else {
                setMappedCode(null);
                setMappedDisplay(null);
                setEquivalence(null);
                setError(result.error || 'Mapeamento não encontrado');
            }
        } catch (err: any) {
            setError(err.message || 'Erro ao mapear código');
            setMappedCode(null);
            setMappedDisplay(null);
            setEquivalence(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const mapSNOMEDToICD10 = useCallback(async (snomedCode: string) => {
        setLoading(true);
        setError(null);

        try {
            const result = await terminologyApi.mapSNOMEDToICD10(snomedCode);
            if (result.mapped) {
                setMappedCode(result.target_code || null);
                setMappedDisplay(result.target_display || null);
                setEquivalence(result.equivalence || null);
            } else {
                setMappedCode(null);
                setMappedDisplay(null);
                setEquivalence(null);
                setError(result.error || 'Mapeamento não encontrado');
            }
        } catch (err: any) {
            setError(err.message || 'Erro ao mapear código');
            setMappedCode(null);
            setMappedDisplay(null);
            setEquivalence(null);
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        mappedCode,
        mappedDisplay,
        equivalence,
        loading,
        error,
        mapICD10ToSNOMED,
        mapSNOMEDToICD10
    };
}
