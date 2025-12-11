/**
 * Sprint 21: MedicationAutocomplete Component
 * 
 * Autocomplete input for searching and selecting medications from RxNorm.
 * Features:
 * - Debounced search
 * - Dropdown with results
 * - Selection callback with RxCUI
 * - Optional drug interaction warnings
 */

import React, { useState, useRef, useEffect } from 'react';
import { useRxNormSearch, useDrugInteractions } from '../../hooks/useTerminology';
import { RxNormResult } from '../../services/terminologyApi';
import './MedicationAutocomplete.css';

export interface SelectedMedication {
    rxcui: string;
    name: string;
    tty?: string;
}

export interface MedicationAutocompleteProps {
    /** Label for the input */
    label?: string;
    /** Placeholder text */
    placeholder?: string;
    /** Called when a medication is selected */
    onSelect: (medication: SelectedMedication) => void;
    /** Called when selection is cleared */
    onClear?: () => void;
    /** Currently selected medications (for interaction checking) */
    currentMedications?: SelectedMedication[];
    /** Whether to check interactions when selecting */
    checkInteractions?: boolean;
    /** Whether the field is required */
    required?: boolean;
    /** Whether the field is disabled */
    disabled?: boolean;
    /** Error message to display */
    error?: string;
    /** Additional CSS class */
    className?: string;
}

export const MedicationAutocomplete: React.FC<MedicationAutocompleteProps> = ({
    label = 'Medicamento',
    placeholder = 'Digite o nome do medicamento...',
    onSelect,
    onClear,
    currentMedications = [],
    checkInteractions = true,
    required = false,
    disabled = false,
    error,
    className = ''
}) => {
    const [inputValue, setInputValue] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const [selectedMedication, setSelectedMedication] = useState<SelectedMedication | null>(null);
    const [showInteractionWarning, setShowInteractionWarning] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const { results, loading, error: searchError, search } = useRxNormSearch(300);
    const {
        interactions,
        hasInteractions,
        loading: checkingInteractions,
        checkInteractions: doCheckInteractions
    } = useDrugInteractions();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Search when input changes
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setInputValue(value);
        setSelectedMedication(null);

        if (value.length >= 2) {
            search(value);
            setIsOpen(true);
        } else {
            setIsOpen(false);
        }
    };

    // Handle medication selection
    const handleSelect = async (result: RxNormResult) => {
        const medication: SelectedMedication = {
            rxcui: result.rxcui,
            name: result.name,
            tty: result.tty
        };

        setSelectedMedication(medication);
        setInputValue(result.name);
        setIsOpen(false);

        // Check for interactions with current medications
        if (checkInteractions && currentMedications.length > 0) {
            const allRxcuis = [...currentMedications.map(m => m.rxcui), result.rxcui];
            await doCheckInteractions(allRxcuis);
            if (hasInteractions) {
                setShowInteractionWarning(true);
            }
        }

        onSelect(medication);
    };

    // Handle clear
    const handleClear = () => {
        setInputValue('');
        setSelectedMedication(null);
        setIsOpen(false);
        setShowInteractionWarning(false);
        inputRef.current?.focus();
        onClear?.();
    };

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setIsOpen(false);
        }
    };

    // Get severity class for interaction badge
    const getSeverityClass = (severity: string): string => {
        switch (severity.toLowerCase()) {
            case 'high':
                return 'medication-autocomplete__severity--high';
            case 'moderate':
                return 'medication-autocomplete__severity--moderate';
            default:
                return 'medication-autocomplete__severity--low';
        }
    };

    return (
        <div
            ref={containerRef}
            className={`medication-autocomplete ${className}`}
            onKeyDown={handleKeyDown}
        >
            {label && (
                <label className="medication-autocomplete__label">
                    {label}
                    {required && <span className="medication-autocomplete__required">*</span>}
                </label>
            )}

            <div className="medication-autocomplete__input-wrapper">
                <input
                    ref={inputRef}
                    type="text"
                    className={`medication-autocomplete__input ${error ? 'medication-autocomplete__input--error' : ''}`}
                    value={inputValue}
                    onChange={handleInputChange}
                    onFocus={() => inputValue.length >= 2 && results.length > 0 && setIsOpen(true)}
                    placeholder={placeholder}
                    disabled={disabled}
                    aria-label={label}
                    aria-expanded={isOpen}
                    aria-haspopup="listbox"
                    autoComplete="off"
                />

                {loading && (
                    <span className="medication-autocomplete__spinner" aria-label="Carregando..." />
                )}

                {selectedMedication && !loading && (
                    <button
                        type="button"
                        className="medication-autocomplete__clear"
                        onClick={handleClear}
                        aria-label="Limpar seleção"
                    >
                        ×
                    </button>
                )}
            </div>

            {/* Dropdown Results */}
            {isOpen && results.length > 0 && (
                <ul className="medication-autocomplete__dropdown" role="listbox">
                    {results.map((result) => (
                        <li
                            key={result.rxcui}
                            className="medication-autocomplete__option"
                            onClick={() => handleSelect(result)}
                            role="option"
                        >
                            <span className="medication-autocomplete__option-name">
                                {result.name}
                            </span>
                            <span className="medication-autocomplete__option-code">
                                RxCUI: {result.rxcui}
                            </span>
                            {result.tty && (
                                <span className="medication-autocomplete__option-type">
                                    {result.tty}
                                </span>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            {/* No Results */}
            {isOpen && !loading && inputValue.length >= 2 && results.length === 0 && (
                <div className="medication-autocomplete__no-results">
                    Nenhum medicamento encontrado
                </div>
            )}

            {/* Error Message */}
            {(error || searchError) && (
                <span className="medication-autocomplete__error">
                    {error || searchError}
                </span>
            )}

            {/* Interaction Warning */}
            {showInteractionWarning && hasInteractions && (
                <div className="medication-autocomplete__warning">
                    <div className="medication-autocomplete__warning-header">
                        <span className="medication-autocomplete__warning-icon">⚠️</span>
                        <strong>Interações Medicamentosas Detectadas</strong>
                        <button
                            type="button"
                            className="medication-autocomplete__warning-close"
                            onClick={() => setShowInteractionWarning(false)}
                            aria-label="Fechar aviso"
                        >
                            ×
                        </button>
                    </div>
                    <ul className="medication-autocomplete__interactions">
                        {interactions.map((interaction, index) => (
                            <li key={index} className="medication-autocomplete__interaction">
                                <span className={`medication-autocomplete__severity ${getSeverityClass(interaction.severity)}`}>
                                    {interaction.severity}
                                </span>
                                <span className="medication-autocomplete__interaction-drugs">
                                    {interaction.drug1} + {interaction.drug2}
                                </span>
                                <p className="medication-autocomplete__interaction-desc">
                                    {interaction.description}
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Checking Interactions Indicator */}
            {checkingInteractions && (
                <div className="medication-autocomplete__checking">
                    Verificando interações...
                </div>
            )}
        </div>
    );
};

export default MedicationAutocomplete;
