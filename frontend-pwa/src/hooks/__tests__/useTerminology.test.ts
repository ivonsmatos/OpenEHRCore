/**
 * Sprint 23: Unit Tests for Terminology Hooks
 * 
 * Tests for useRxNormSearch, useICD10Search, useTUSSSearch, and useTerminologyMapping
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import {
    useRxNormSearch,
    useICD10Search,
    useTUSSSearch,
    useDrugInteractions,
    useTerminologyMapping
} from '../useTerminology';
import terminologyApi from '../../services/terminologyApi';

// Mock the API
vi.mock('../../services/terminologyApi', () => ({
    default: {
        searchRxNorm: vi.fn(),
        searchICD10: vi.fn(),
        searchTUSS: vi.fn(),
        checkMultiDrugInteractions: vi.fn(),
        mapICD10ToSNOMED: vi.fn(),
        mapSNOMEDToICD10: vi.fn()
    }
}));

describe('useRxNormSearch', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize with empty state', () => {
        const { result } = renderHook(() => useRxNormSearch());

        expect(result.current.results).toEqual([]);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    it('should not search with query less than 2 chars', async () => {
        const { result } = renderHook(() => useRxNormSearch(100));

        act(() => {
            result.current.search('a');
        });

        await waitFor(() => {
            expect(terminologyApi.searchRxNorm).not.toHaveBeenCalled();
        });
    });

    it('should search with valid query', async () => {
        const mockResults = [
            { rxcui: '1191', name: 'Aspirin', score: 100, tty: 'IN', synonym: '' }
        ];
        vi.mocked(terminologyApi.searchRxNorm).mockResolvedValue(mockResults);

        const { result } = renderHook(() => useRxNormSearch(50));

        act(() => {
            result.current.search('aspirin');
        });

        await waitFor(() => {
            expect(result.current.results).toEqual(mockResults);
        });
    });

    it('should handle search error', async () => {
        vi.mocked(terminologyApi.searchRxNorm).mockRejectedValue(new Error('API Error'));

        const { result } = renderHook(() => useRxNormSearch(50));

        act(() => {
            result.current.search('aspirin');
        });

        await waitFor(() => {
            expect(result.current.error).toBeTruthy();
            expect(result.current.results).toEqual([]);
        });
    });
});

describe('useICD10Search', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should search ICD-10 codes', async () => {
        const mockResults = [
            { code: 'I10', description: 'Hypertension', category: 'Circulatory', system: 'icd10' }
        ];
        vi.mocked(terminologyApi.searchICD10).mockResolvedValue(mockResults);

        const { result } = renderHook(() => useICD10Search(50));

        act(() => {
            result.current.search('hypertension');
        });

        await waitFor(() => {
            expect(result.current.results).toEqual(mockResults);
        });
    });
});

describe('useTUSSSearch', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should search TUSS codes', async () => {
        const mockResults = [
            { code: '10101012', description: 'Consulta', type: 'consulta', category: 'Consulta', system: 'tuss' }
        ];
        vi.mocked(terminologyApi.searchTUSS).mockResolvedValue(mockResults);

        const { result } = renderHook(() => useTUSSSearch(50));

        act(() => {
            result.current.search('consulta');
        });

        await waitFor(() => {
            expect(result.current.results).toEqual(mockResults);
        });
    });

    it('should search with type filter', async () => {
        vi.mocked(terminologyApi.searchTUSS).mockResolvedValue([]);

        const { result } = renderHook(() => useTUSSSearch(50));

        act(() => {
            result.current.search('hemograma', 'exame');
        });

        await waitFor(() => {
            expect(terminologyApi.searchTUSS).toHaveBeenCalled();
        });
    });
});

describe('useDrugInteractions', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize with empty state', () => {
        const { result } = renderHook(() => useDrugInteractions());

        expect(result.current.interactions).toEqual([]);
        expect(result.current.hasInteractions).toBe(false);
        expect(result.current.loading).toBe(false);
    });

    it('should not check with less than 2 drugs', async () => {
        const { result } = renderHook(() => useDrugInteractions());

        await act(async () => {
            await result.current.checkInteractions(['single-drug']);
        });

        expect(terminologyApi.checkMultiDrugInteractions).not.toHaveBeenCalled();
    });

    it('should check interactions with multiple drugs', async () => {
        const mockResult = {
            hasInteractions: true,
            interactions: [
                { drug1: 'Aspirin', drug1_rxcui: '1191', drug2: 'Warfarin', drug2_rxcui: '855', severity: 'high', description: 'Bleeding risk' }
            ]
        };
        vi.mocked(terminologyApi.checkMultiDrugInteractions).mockResolvedValue(mockResult);

        const { result } = renderHook(() => useDrugInteractions());

        await act(async () => {
            await result.current.checkInteractions(['1191', '855']);
        });

        expect(result.current.hasInteractions).toBe(true);
        expect(result.current.interactions.length).toBe(1);
    });
});

describe('useTerminologyMapping', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should map ICD-10 to SNOMED', async () => {
        vi.mocked(terminologyApi.mapICD10ToSNOMED).mockResolvedValue({
            mapped: true,
            target_code: '38341003',
            target_display: 'Hypertensive disorder',
            equivalence: 'equivalent'
        });

        const { result } = renderHook(() => useTerminologyMapping());

        await act(async () => {
            await result.current.mapICD10ToSNOMED('I10');
        });

        expect(result.current.mappedCode).toBe('38341003');
        expect(result.current.mappedDisplay).toBe('Hypertensive disorder');
    });

    it('should handle mapping not found', async () => {
        vi.mocked(terminologyApi.mapICD10ToSNOMED).mockResolvedValue({
            mapped: false,
            error: 'No mapping found'
        });

        const { result } = renderHook(() => useTerminologyMapping());

        await act(async () => {
            await result.current.mapICD10ToSNOMED('ZZZZZ');
        });

        expect(result.current.mappedCode).toBeNull();
        expect(result.current.error).toBeTruthy();
    });

    it('should map SNOMED to ICD-10', async () => {
        vi.mocked(terminologyApi.mapSNOMEDToICD10).mockResolvedValue({
            mapped: true,
            target_code: 'I10',
            target_display: 'Essential hypertension',
            equivalence: 'equivalent'
        });

        const { result } = renderHook(() => useTerminologyMapping());

        await act(async () => {
            await result.current.mapSNOMEDToICD10('38341003');
        });

        expect(result.current.mappedCode).toBe('I10');
    });
});
