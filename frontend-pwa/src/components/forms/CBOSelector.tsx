import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';

interface CBOOcupacao {
    codigo: string;
    nome: string;
    familia: string;
    familia_nome: string;
    descricao: string;
}

interface CBOSelectorProps {
    value?: string;
    onChange: (codigo: string, ocupacao?: CBOOcupacao) => void;
    placeholder?: string;
    familiaFilter?: string; // e.g., '2251' for doctors only
    className?: string;
}

export const CBOSelector: React.FC<CBOSelectorProps> = ({
    value,
    onChange,
    placeholder = 'Buscar ocupação CBO...',
    familiaFilter,
    className = ''
}) => {
    const [search, setSearch] = useState('');
    const [results, setResults] = useState<CBOOcupacao[]>([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedOcupacao, setSelectedOcupacao] = useState<CBOOcupacao | null>(null);
    const [families, setFamilies] = useState<{ codigo: string; nome: string }[]>([]);
    const [selectedFamily, setSelectedFamily] = useState(familiaFilter || '');

    // Load families on mount
    useEffect(() => {
        loadFamilies();
        if (familiaFilter) {
            loadByFamily(familiaFilter);
        }
    }, [familiaFilter]);

    // Load selected value details
    useEffect(() => {
        if (value && !selectedOcupacao) {
            loadOcupacao(value);
        }
    }, [value]);

    const loadFamilies = async () => {
        try {
            const res = await api.get('/cbo/families/');
            setFamilies(res.data.results || []);
        } catch (err) {
            console.error('Erro ao carregar famílias CBO:', err);
        }
    };

    const loadOcupacao = async (codigo: string) => {
        try {
            const res = await api.get(`/cbo/${codigo}/`);
            setSelectedOcupacao(res.data);
        } catch (err) {
            console.error('Erro ao carregar ocupação:', err);
        }
    };

    const loadByFamily = async (familia: string) => {
        try {
            setLoading(true);
            const res = await api.get(`/cbo/search/?family=${familia}`);
            setResults(res.data.results || []);
        } catch (err) {
            console.error('Erro ao carregar ocupações:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = useCallback(async (term: string) => {
        if (term.length < 2) {
            setResults([]);
            return;
        }

        try {
            setLoading(true);
            let url = `/cbo/search/?q=${encodeURIComponent(term)}`;
            if (selectedFamily) {
                url += `&family=${selectedFamily}`;
            }
            const res = await api.get(url);
            setResults(res.data.results || []);
            setShowDropdown(true);
        } catch (err) {
            console.error('Erro na busca CBO:', err);
        } finally {
            setLoading(false);
        }
    }, [selectedFamily]);

    const handleFamilyChange = (familia: string) => {
        setSelectedFamily(familia);
        if (familia) {
            loadByFamily(familia);
            setShowDropdown(true);
        } else {
            setResults([]);
        }
    };

    const handleSelect = (ocupacao: CBOOcupacao) => {
        setSelectedOcupacao(ocupacao);
        setSearch('');
        setShowDropdown(false);
        onChange(ocupacao.codigo, ocupacao);
    };

    const handleClear = () => {
        setSelectedOcupacao(null);
        setSearch('');
        setResults([]);
        onChange('', undefined);
    };

    return (
        <div className={`cbo-selector ${className}`}>
            {/* Family filter */}
            {!familiaFilter && (
                <div className="family-filter">
                    <select
                        value={selectedFamily}
                        onChange={(e) => handleFamilyChange(e.target.value)}
                        aria-label="Filtrar por família CBO"
                    >
                        <option value="">Todas as categorias</option>
                        {families.map(f => (
                            <option key={f.codigo} value={f.codigo}>
                                {f.codigo} - {f.nome}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Selected value display */}
            {selectedOcupacao ? (
                <div className="selected-cbo">
                    <div className="cbo-info">
                        <span className="cbo-code">{selectedOcupacao.codigo}</span>
                        <span className="cbo-name">{selectedOcupacao.nome}</span>
                        <span className="cbo-family">{selectedOcupacao.familia_nome}</span>
                    </div>
                    <button
                        type="button"
                        className="clear-btn"
                        onClick={handleClear}
                        aria-label="Limpar seleção"
                    >
                        ×
                    </button>
                </div>
            ) : (
                <div className="search-container">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            handleSearch(e.target.value);
                        }}
                        onFocus={() => results.length > 0 && setShowDropdown(true)}
                        placeholder={placeholder}
                        aria-label="Buscar ocupação CBO"
                    />
                    {loading && <span className="loading-indicator">⏳</span>}
                </div>
            )}

            {/* Dropdown results */}
            {showDropdown && results.length > 0 && !selectedOcupacao && (
                <ul className="cbo-dropdown" role="listbox">
                    {results.map(ocupacao => (
                        <li
                            key={ocupacao.codigo}
                            onClick={() => handleSelect(ocupacao)}
                            role="option"
                            aria-selected={value === ocupacao.codigo}
                        >
                            <span className="code">{ocupacao.codigo}</span>
                            <div className="details">
                                <span className="name">{ocupacao.nome}</span>
                                <span className="desc">{ocupacao.descricao}</span>
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            {/* Quick access buttons */}
            {!selectedOcupacao && !showDropdown && (
                <div className="quick-access">
                    <button type="button" onClick={() => handleFamilyChange('2251')}>
                        👨‍⚕️ Médicos
                    </button>
                    <button type="button" onClick={() => handleFamilyChange('2235')}>
                        👩‍⚕️ Enfermeiros
                    </button>
                    <button type="button" onClick={() => handleFamilyChange('2232')}>
                        🦷 Dentistas
                    </button>
                    <button type="button" onClick={() => handleFamilyChange('3222')}>
                        💉 Técnicos Enf.
                    </button>
                </div>
            )}

            <style>{`
        .cbo-selector {
          position: relative;
          width: 100%;
        }

        .family-filter {
          margin-bottom: 0.5rem;
        }

        .family-filter select {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 6px;
          font-size: 0.875rem;
          background: var(--color-surface, white);
        }

        .search-container {
          position: relative;
        }

        .search-container input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 8px;
          font-size: 1rem;
        }

        .search-container input:focus {
          outline: none;
          border-color: var(--color-primary, #0468BF);
          box-shadow: 0 0 0 2px rgba(4, 104, 191, 0.1);
        }

        .loading-indicator {
          position: absolute;
          right: 0.75rem;
          top: 50%;
          transform: translateY(-50%);
        }

        .selected-cbo {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem;
          background: var(--color-primary-light, #e0f2fe);
          border: 1px solid var(--color-primary, #0468BF);
          border-radius: 8px;
        }

        .cbo-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .cbo-code {
          font-weight: 600;
          color: var(--color-primary, #0468BF);
          font-size: 0.875rem;
        }

        .cbo-name {
          font-weight: 500;
        }

        .cbo-family {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #6b7280);
        }

        .clear-btn {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: var(--color-text-secondary, #6b7280);
          padding: 0 0.5rem;
        }

        .clear-btn:hover {
          color: var(--color-error, #dc2626);
        }

        .cbo-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          max-height: 300px;
          overflow-y: auto;
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          list-style: none;
          padding: 0;
          margin: 0.25rem 0 0;
          z-index: 100;
        }

        .cbo-dropdown li {
          display: flex;
          gap: 0.75rem;
          padding: 0.75rem;
          cursor: pointer;
          border-bottom: 1px solid var(--color-border, #e5e7eb);
        }

        .cbo-dropdown li:last-child {
          border-bottom: none;
        }

        .cbo-dropdown li:hover {
          background: var(--color-background, #f9fafb);
        }

        .cbo-dropdown .code {
          background: var(--color-primary, #0468BF);
          color: white;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 600;
          white-space: nowrap;
          height: fit-content;
        }

        .cbo-dropdown .details {
          display: flex;
          flex-direction: column;
        }

        .cbo-dropdown .name {
          font-weight: 500;
        }

        .cbo-dropdown .desc {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #6b7280);
        }

        .quick-access {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
          flex-wrap: wrap;
        }

        .quick-access button {
          background: var(--color-surface, white);
          border: 1px solid var(--color-border, #e5e7eb);
          padding: 0.375rem 0.75rem;
          border-radius: 999px;
          font-size: 0.75rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .quick-access button:hover {
          background: var(--color-primary, #0468BF);
          color: white;
          border-color: var(--color-primary, #0468BF);
        }
      `}</style>
        </div>
    );
};

export default CBOSelector;
