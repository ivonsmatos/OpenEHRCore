import React, { useState, useCallback } from 'react';
import './AdvancedFilters.css';

export interface FilterOption {
    value: string;
    label: string;
}

export interface FilterConfig {
    /** Unique key for the filter */
    key: string;
    /** Display label */
    label: string;
    /** Filter type */
    type: 'text' | 'select' | 'date' | 'daterange' | 'multiselect';
    /** Options for select/multiselect */
    options?: FilterOption[];
    /** Placeholder text */
    placeholder?: string;
}

export interface AdvancedFiltersProps {
    /** Filter configurations */
    filters: FilterConfig[];
    /** Current filter values */
    values: Record<string, any>;
    /** Called when filter values change */
    onChange: (values: Record<string, any>) => void;
    /** Called when Apply button is clicked */
    onApply: () => void;
    /** Called when Clear button is clicked */
    onClear: () => void;
    /** Whether filters panel is initially collapsed */
    defaultCollapsed?: boolean;
    /** Additional CSS class */
    className?: string;
}

/**
 * AdvancedFilters Component
 * 
 * A collapsible filter panel supporting:
 * - Date range picker
 * - Dropdown selects
 * - Multi-select support
 * - Apply/Clear buttons
 */
export const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
    filters,
    values,
    onChange,
    onApply,
    onClear,
    defaultCollapsed = true,
    className = ''
}) => {
    const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

    const handleToggle = useCallback(() => {
        setIsCollapsed(prev => !prev);
    }, []);

    const handleValueChange = useCallback((key: string, value: any) => {
        onChange({ ...values, [key]: value });
    }, [values, onChange]);

    const handleClear = useCallback(() => {
        const clearedValues: Record<string, any> = {};
        filters.forEach(filter => {
            clearedValues[filter.key] = filter.type === 'multiselect' ? [] : '';
        });
        onChange(clearedValues);
        onClear();
    }, [filters, onChange, onClear]);

    const renderFilter = (filter: FilterConfig) => {
        const value = values[filter.key] ?? '';

        switch (filter.type) {
            case 'text':
                return (
                    <input
                        type="text"
                        className="advanced-filters__input"
                        placeholder={filter.placeholder}
                        value={value}
                        onChange={(e) => handleValueChange(filter.key, e.target.value)}
                    />
                );

            case 'select':
                return (
                    <select
                        className="advanced-filters__select"
                        value={value}
                        onChange={(e) => handleValueChange(filter.key, e.target.value)}
                        aria-label={filter.label}
                    >
                        <option value="">{filter.placeholder || 'Selecione...'}</option>
                        {filter.options?.map(opt => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                );

            case 'date':
                return (
                    <input
                        type="date"
                        className="advanced-filters__date"
                        value={value}
                        onChange={(e) => handleValueChange(filter.key, e.target.value)}
                        aria-label={filter.label}
                    />
                );

            case 'daterange':
                const [startDate, endDate] = value ? value.split(',') : ['', ''];
                return (
                    <div className="advanced-filters__daterange">
                        <input
                            type="date"
                            className="advanced-filters__date"
                            value={startDate}
                            onChange={(e) => handleValueChange(filter.key, `${e.target.value},${endDate}`)}
                            placeholder="Data início"
                        />
                        <span className="advanced-filters__daterange-separator">até</span>
                        <input
                            type="date"
                            className="advanced-filters__date"
                            value={endDate}
                            onChange={(e) => handleValueChange(filter.key, `${startDate},${e.target.value}`)}
                            placeholder="Data fim"
                        />
                    </div>
                );

            case 'multiselect':
                const selectedValues = Array.isArray(value) ? value : [];
                return (
                    <div className="advanced-filters__multiselect">
                        {filter.options?.map(opt => (
                            <label key={opt.value} className="advanced-filters__checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={selectedValues.includes(opt.value)}
                                    onChange={(e) => {
                                        const newValues = e.target.checked
                                            ? [...selectedValues, opt.value]
                                            : selectedValues.filter((v: string) => v !== opt.value);
                                        handleValueChange(filter.key, newValues);
                                    }}
                                />
                                <span>{opt.label}</span>
                            </label>
                        ))}
                    </div>
                );

            default:
                return null;
        }
    };

    const hasActiveFilters = Object.values(values).some(v =>
        Array.isArray(v) ? v.length > 0 : Boolean(v)
    );

    return (
        <div className={`advanced-filters ${className} ${isCollapsed ? 'advanced-filters--collapsed' : ''}`}>
            <button
                type="button"
                className="advanced-filters__toggle"
                onClick={handleToggle}
                aria-expanded={!isCollapsed ? "true" : "false"}
            >
                <span className="advanced-filters__toggle-icon">
                    {isCollapsed ? '▼' : '▲'}
                </span>
                <span>Filtros Avançados</span>
                {hasActiveFilters && (
                    <span className="advanced-filters__badge">
                        {Object.values(values).filter(v => Array.isArray(v) ? v.length > 0 : Boolean(v)).length}
                    </span>
                )}
            </button>

            {!isCollapsed && (
                <div className="advanced-filters__panel">
                    <div className="advanced-filters__grid">
                        {filters.map(filter => (
                            <div key={filter.key} className="advanced-filters__field">
                                <label className="advanced-filters__label">
                                    {filter.label}
                                </label>
                                {renderFilter(filter)}
                            </div>
                        ))}
                    </div>

                    <div className="advanced-filters__actions">
                        <button
                            type="button"
                            className="advanced-filters__btn advanced-filters__btn--clear"
                            onClick={handleClear}
                        >
                            Limpar
                        </button>
                        <button
                            type="button"
                            className="advanced-filters__btn advanced-filters__btn--apply"
                            onClick={onApply}
                        >
                            Aplicar Filtros
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdvancedFilters;
