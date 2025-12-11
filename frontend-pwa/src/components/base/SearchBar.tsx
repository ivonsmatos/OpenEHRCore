import React, { useState, useCallback } from 'react';
import { useDebounce } from '../../hooks/useDebounce';
import './SearchBar.css';

export interface SearchBarProps {
    /** Placeholder text for the input */
    placeholder?: string;
    /** Callback when search value changes (debounced) */
    onSearch: (query: string) => void;
    /** Debounce delay in milliseconds */
    debounceMs?: number;
    /** Whether the search is loading */
    loading?: boolean;
    /** Initial value */
    initialValue?: string;
    /** Additional CSS class */
    className?: string;
}

/**
 * SearchBar Component
 * 
 * A reusable search input with:
 * - Debounced input (default 300ms)
 * - Loading indicator
 * - Clear button
 * - Keyboard navigation (Enter to search)
 * - Accessible (ARIA labels)
 */
export const SearchBar: React.FC<SearchBarProps> = ({
    placeholder = 'Buscar...',
    onSearch,
    debounceMs = 300,
    loading = false,
    initialValue = '',
    className = ''
}) => {
    const [inputValue, setInputValue] = useState(initialValue);
    const debouncedValue = useDebounce(inputValue, debounceMs);

    // Call onSearch when debounced value changes
    React.useEffect(() => {
        onSearch(debouncedValue);
    }, [debouncedValue, onSearch]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    }, []);

    const handleClear = useCallback(() => {
        setInputValue('');
        onSearch('');
    }, [onSearch]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            onSearch(inputValue);
        }
        if (e.key === 'Escape') {
            handleClear();
        }
    }, [inputValue, onSearch, handleClear]);

    return (
        <div className={`search-bar ${className}`}>
            <div className="search-bar__container">
                <span className="search-bar__icon" aria-hidden="true">
                    🔍
                </span>

                <input
                    type="text"
                    className="search-bar__input"
                    placeholder={placeholder}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    aria-label={placeholder}
                />

                {loading && (
                    <span className="search-bar__loader" aria-label="Carregando...">
                        <span className="search-bar__spinner"></span>
                    </span>
                )}

                {inputValue && !loading && (
                    <button
                        type="button"
                        className="search-bar__clear"
                        onClick={handleClear}
                        aria-label="Limpar busca"
                    >
                        ✕
                    </button>
                )}
            </div>
        </div>
    );
};

export default SearchBar;
