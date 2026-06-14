/**
 * CRM Validation Component
 *
 * Sprint 39: Validacao de registros em conselhos profissionais (CRM, COREN, etc.)
 * Segue padroes LGPD, FHIR R4, GDPR.
 *
 * Features:
 * - Validacao de formato em tempo real
 * - Integracao com API de validacao
 * - Feedback visual de status
 * - Acessibilidade WCAG 2.1 AA
 */

import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { Check, X, AlertCircle, Loader2, Shield, Info } from 'lucide-react';
import { colors, spacing, borderRadius, shadows, transitions } from '../../theme/colors';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Tipos de conselho suportados
const CONSELHOS = [
    { codigo: 'CRM', descricao: 'Conselho Regional de Medicina' },
    { codigo: 'COREN', descricao: 'Conselho Regional de Enfermagem' },
    { codigo: 'CRO', descricao: 'Conselho Regional de Odontologia' },
    { codigo: 'CRF', descricao: 'Conselho Regional de Farmacia' },
    { codigo: 'CREFITO', descricao: 'Conselho Regional de Fisioterapia' },
    { codigo: 'CRN', descricao: 'Conselho Regional de Nutricao' },
    { codigo: 'CRFa', descricao: 'Conselho Regional de Fonoaudiologia' },
    { codigo: 'CRP', descricao: 'Conselho Regional de Psicologia' },
    { codigo: 'CRBM', descricao: 'Conselho Regional de Biomedicina' },
    { codigo: 'CRESS', descricao: 'Conselho Regional de Servico Social' },
];

// UFs validas
const UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

// Status de validacao
type ValidationStatus = 'idle' | 'validating' | 'valid' | 'invalid_format' | 'not_found' | 'suspended' | 'cancelled' | 'expired' | 'error';

interface ValidationResult {
    status: ValidationStatus;
    conselho: string;
    numero: string;
    uf: string;
    nome_profissional?: string;
    especialidades?: string[];
    situacao_registro?: string;
    validation_id?: string;
    validated_at?: string;
    validation_source?: string;
    message?: string;
    fhir_identifier?: Record<string, unknown>;
}

interface CRMValidationProps {
    /** Tipo de conselho inicial */
    initialConselho?: string;
    /** Numero inicial */
    initialNumero?: string;
    /** UF inicial */
    initialUf?: string;
    /** Callback quando validacao muda */
    onValidationChange?: (result: ValidationResult | null) => void;
    /** Callback para obter os valores atuais */
    onChange?: (values: { conselho: string; numero: string; uf: string }) => void;
    /** Se deve validar automaticamente ao digitar */
    autoValidate?: boolean;
    /** Delay em ms para auto-validacao */
    autoValidateDelay?: number;
    /** Se campos sao obrigatorios */
    required?: boolean;
    /** Se componente esta desabilitado */
    disabled?: boolean;
    /** Mostrar badge de status */
    showStatusBadge?: boolean;
    /** Mostrar info do profissional quando validado via API */
    showProfessionalInfo?: boolean;
}

/**
 * CRM Validation Component
 *
 * @example
 * <CRMValidation
 *   initialConselho="CRM"
 *   initialUf="SP"
 *   onValidationChange={(result) => console.log(result)}
 *   autoValidate
 * />
 */
const CRMValidation: React.FC<CRMValidationProps> = ({
    initialConselho = 'CRM',
    initialNumero = '',
    initialUf = 'SP',
    onValidationChange,
    onChange,
    autoValidate = false,
    autoValidateDelay = 1000,
    required = false,
    disabled = false,
    showStatusBadge = true,
    showProfessionalInfo = true,
}) => {
    // Estado do formulario
    const [conselho, setConselho] = useState(initialConselho);
    const [numero, setNumero] = useState(initialNumero);
    const [uf, setUf] = useState(initialUf);

    // Estado de validacao
    const [validationStatus, setValidationStatus] = useState<ValidationStatus>('idle');
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Debounce timer para auto-validacao
    const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

    // Notificar mudancas
    useEffect(() => {
        if (onChange) {
            onChange({ conselho, numero, uf });
        }
    }, [conselho, numero, uf, onChange]);

    // Validacao de formato local
    const validateFormat = useCallback((num: string, cons: string): boolean => {
        if (!num || num.length < 4) return false;

        // Remover nao-digitos
        const cleanNum = num.replace(/\D/g, '');

        // Validar tamanho por tipo de conselho
        const minMax: Record<string, [number, number]> = {
            CRM: [4, 7],
            COREN: [4, 9],
            CRO: [4, 7],
            CRF: [4, 6],
            CREFITO: [4, 7],
            CRN: [4, 6],
            CRFa: [4, 6],
            CRP: [4, 8],
            CRBM: [4, 6],
            CRESS: [4, 6],
        };

        const [min, max] = minMax[cons] || [4, 7];
        return cleanNum.length >= min && cleanNum.length <= max;
    }, []);

    // Funcao de validacao via API
    const validate = useCallback(async () => {
        // Validar formato primeiro
        if (!validateFormat(numero, conselho)) {
            setValidationStatus('invalid_format');
            setValidationResult(null);
            setError('Formato do numero invalido');
            if (onValidationChange) {
                onValidationChange(null);
            }
            return;
        }

        setValidationStatus('validating');
        setError(null);

        try {
            const response = await axios.post(`${API_URL}/crm/validate/`, {
                conselho,
                numero,
                uf,
                use_api: true,
            });

            const result: ValidationResult = response.data;
            setValidationResult(result);
            setValidationStatus(result.status as ValidationStatus);

            if (onValidationChange) {
                onValidationChange(result);
            }
        } catch (err: unknown) {
            const axiosError = err as { response?: { data?: { message?: string; error?: string } } };
            if (axiosError.response?.data) {
                const data = axiosError.response.data;
                setValidationStatus(data.message?.includes('not found') ? 'not_found' : 'error');
                setError(data.message || data.error || 'Erro na validacao');
            } else {
                setValidationStatus('error');
                setError('Erro de conexao com o servidor');
            }
            setValidationResult(null);
            if (onValidationChange) {
                onValidationChange(null);
            }
        }
    }, [conselho, numero, uf, validateFormat, onValidationChange]);

    // Auto-validacao com debounce
    useEffect(() => {
        if (!autoValidate || !numero || numero.length < 4) {
            return;
        }

        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }

        const timer = setTimeout(() => {
            validate();
        }, autoValidateDelay);

        setDebounceTimer(timer);

        return () => {
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
        };
    }, [autoValidate, numero, conselho, uf, autoValidateDelay]); // eslint-disable-line react-hooks/exhaustive-deps

    // Estilos
    const inputStyle: React.CSSProperties = {
        width: '100%',
        padding: spacing.sm,
        border: `1px solid ${colors.border.light}`,
        borderRadius: borderRadius.md,
        fontSize: '1rem',
        fontFamily: 'inherit',
        transition: `all ${transitions.base}`,
        outline: 'none',
    };

    const inputFocusStyle: React.CSSProperties = {
        borderColor: colors.primary.medium,
        boxShadow: `0 0 0 3px ${colors.primary.light}40`,
    };

    const labelStyle: React.CSSProperties = {
        display: 'block',
        marginBottom: spacing.xs,
        fontWeight: 500,
        color: colors.text.primary,
        fontSize: '0.875rem',
    };

    // Obter estilo do badge de status
    const getStatusBadgeStyle = (): React.CSSProperties => {
        const baseStyle: React.CSSProperties = {
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 10px',
            borderRadius: borderRadius.full,
            fontSize: '0.75rem',
            fontWeight: 600,
        };

        switch (validationStatus) {
            case 'valid':
                return { ...baseStyle, backgroundColor: '#dcfce7', color: '#166534' };
            case 'invalid_format':
            case 'not_found':
            case 'error':
                return { ...baseStyle, backgroundColor: '#fee2e2', color: '#991b1b' };
            case 'suspended':
            case 'cancelled':
            case 'expired':
                return { ...baseStyle, backgroundColor: '#fef3c7', color: '#92400e' };
            case 'validating':
                return { ...baseStyle, backgroundColor: '#e0e7ff', color: '#3730a3' };
            default:
                return { ...baseStyle, backgroundColor: '#f3f4f6', color: '#6b7280' };
        }
    };

    // Obter texto do status
    const getStatusText = (): string => {
        switch (validationStatus) {
            case 'valid':
                return 'Valido';
            case 'invalid_format':
                return 'Formato invalido';
            case 'not_found':
                return 'Nao encontrado';
            case 'suspended':
                return 'Suspenso';
            case 'cancelled':
                return 'Cancelado';
            case 'expired':
                return 'Expirado';
            case 'validating':
                return 'Validando...';
            case 'error':
                return 'Erro';
            default:
                return 'Nao validado';
        }
    };

    // Obter icone do status
    const getStatusIcon = () => {
        switch (validationStatus) {
            case 'valid':
                return <Check size={14} />;
            case 'invalid_format':
            case 'not_found':
            case 'error':
                return <X size={14} />;
            case 'suspended':
            case 'cancelled':
            case 'expired':
                return <AlertCircle size={14} />;
            case 'validating':
                return <Loader2 size={14} className="animate-spin" />;
            default:
                return <Info size={14} />;
        }
    };

    return (
        <div style={{ position: 'relative' }}>
            {/* Label */}
            <label style={labelStyle}>
                Registro Profissional {required && <span style={{ color: colors.alert.critical }}>*</span>}
            </label>

            {/* Campos */}
            <div style={{ display: 'flex', gap: spacing.sm, alignItems: 'flex-start' }}>
                {/* Tipo de Conselho */}
                <div style={{ flex: '0 0 130px' }}>
                    <select
                        value={conselho}
                        onChange={(e) => {
                            setConselho(e.target.value);
                            setValidationStatus('idle');
                            setValidationResult(null);
                        }}
                        style={inputStyle}
                        disabled={disabled}
                        aria-label="Tipo de conselho profissional"
                    >
                        {CONSELHOS.map((c) => (
                            <option key={c.codigo} value={c.codigo}>
                                {c.codigo}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Numero do Registro */}
                <div style={{ flex: 1 }}>
                    <input
                        type="text"
                        value={numero}
                        onChange={(e) => {
                            // Permitir apenas digitos
                            const value = e.target.value.replace(/\D/g, '');
                            setNumero(value);
                            setValidationStatus('idle');
                            setValidationResult(null);
                        }}
                        placeholder="Numero (ex: 123456)"
                        style={{
                            ...inputStyle,
                            borderColor: validationStatus === 'valid'
                                ? colors.alert.success
                                : validationStatus === 'invalid_format' || validationStatus === 'not_found' || validationStatus === 'error'
                                    ? colors.alert.critical
                                    : colors.border.light,
                        }}
                        disabled={disabled}
                        aria-label="Numero do registro profissional"
                        aria-invalid={validationStatus === 'invalid_format' || validationStatus === 'not_found'}
                        aria-describedby={error ? 'crm-error' : undefined}
                    />
                </div>

                {/* UF */}
                <div style={{ flex: '0 0 80px' }}>
                    <select
                        value={uf}
                        onChange={(e) => {
                            setUf(e.target.value);
                            setValidationStatus('idle');
                            setValidationResult(null);
                        }}
                        style={inputStyle}
                        disabled={disabled}
                        aria-label="UF do conselho"
                    >
                        {UFS.map((state) => (
                            <option key={state} value={state}>
                                {state}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Botao de Validar */}
                <button
                    type="button"
                    onClick={validate}
                    disabled={disabled || validationStatus === 'validating' || !numero || numero.length < 4}
                    style={{
                        flex: '0 0 auto',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        padding: `${spacing.sm} ${spacing.md}`,
                        backgroundColor: validationStatus === 'valid' ? colors.alert.success : colors.primary.medium,
                        color: 'white',
                        border: 'none',
                        borderRadius: borderRadius.md,
                        fontWeight: 500,
                        cursor: disabled || validationStatus === 'validating' || !numero || numero.length < 4 ? 'not-allowed' : 'pointer',
                        opacity: disabled || validationStatus === 'validating' || !numero || numero.length < 4 ? 0.6 : 1,
                        transition: `all ${transitions.base}`,
                    }}
                    aria-label="Validar registro profissional"
                    aria-busy={validationStatus === 'validating'}
                >
                    {validationStatus === 'validating' ? (
                        <Loader2 size={16} className="animate-spin" />
                    ) : validationStatus === 'valid' ? (
                        <Check size={16} />
                    ) : (
                        <Shield size={16} />
                    )}
                    {validationStatus === 'validating' ? 'Validando' : validationStatus === 'valid' ? 'Validado' : 'Validar'}
                </button>
            </div>

            {/* Status Badge */}
            {showStatusBadge && validationStatus !== 'idle' && (
                <div style={{ marginTop: spacing.xs }}>
                    <span style={getStatusBadgeStyle()}>
                        {getStatusIcon()}
                        {getStatusText()}
                    </span>
                </div>
            )}

            {/* Mensagem de Erro */}
            {error && (
                <div
                    id="crm-error"
                    role="alert"
                    style={{
                        marginTop: spacing.xs,
                        color: colors.alert.critical,
                        fontSize: '0.85rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                    }}
                >
                    <AlertCircle size={14} />
                    {error}
                </div>
            )}

            {/* Info do Profissional (quando validado via API) */}
            {showProfessionalInfo && validationResult && validationResult.status === 'valid' && validationResult.nome_profissional && (
                <div
                    style={{
                        marginTop: spacing.sm,
                        padding: spacing.sm,
                        backgroundColor: '#f0fdf4',
                        border: `1px solid ${colors.alert.success}`,
                        borderRadius: borderRadius.md,
                    }}
                >
                    <div style={{ fontWeight: 600, color: '#166534', marginBottom: '4px' }}>
                        {validationResult.nome_profissional}
                    </div>
                    {validationResult.especialidades && validationResult.especialidades.length > 0 && (
                        <div style={{ fontSize: '0.85rem', color: '#15803d' }}>
                            Especialidades: {validationResult.especialidades.join(', ')}
                        </div>
                    )}
                    {validationResult.situacao_registro && (
                        <div style={{ fontSize: '0.75rem', color: '#16a34a', marginTop: '4px' }}>
                            Situacao: {validationResult.situacao_registro}
                        </div>
                    )}
                    <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '4px' }}>
                        Validado em: {new Date(validationResult.validated_at || '').toLocaleString('pt-BR')}
                        {' | '}
                        Fonte: {validationResult.validation_source === 'api' ? 'CFM' : 'Local'}
                    </div>
                </div>
            )}

            {/* Info de Compliance */}
            {validationStatus !== 'idle' && (
                <div
                    style={{
                        marginTop: spacing.xs,
                        fontSize: '0.7rem',
                        color: colors.text.tertiary,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                    }}
                >
                    <Shield size={12} />
                    Validacao conforme LGPD Art. 6 e 7 | FHIR R4 | GDPR Art. 5
                </div>
            )}
        </div>
    );
};

export default CRMValidation;
