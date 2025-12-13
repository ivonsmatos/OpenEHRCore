import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { colors, spacing, borderRadius } from '../../theme/colors';
import { PractitionerFormData } from '../../types/practitioner';
import Button from '../base/Button';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';


interface CBOOcupacao {
    codigo: string;
    nome: string;
    familia: string;
    familia_nome: string;
    descricao: string;
}

interface PractitionerFormProps {
    onSubmit: (data: PractitionerFormData) => Promise<void>;
    onCancel: () => void;
    initialData?: Partial<PractitionerFormData>;
}

const PractitionerForm: React.FC<PractitionerFormProps> = ({ onSubmit, onCancel, initialData }) => {
    const [formData, setFormData] = useState<PractitionerFormData>({
        family_name: initialData?.family_name || '',
        given_names: initialData?.given_names || [''],
        prefix: initialData?.prefix || '',
        gender: initialData?.gender || 'unknown',
        birthDate: initialData?.birthDate || '',
        phone: initialData?.phone || '',
        email: initialData?.email || '',
        crm: initialData?.crm || '',
        qualification_code: initialData?.qualification_code || 'MD',
        qualification_display: initialData?.qualification_display || '',
        // New CBO fields
        conselho: (initialData as any)?.conselho || 'CRM',
        numero_conselho: (initialData as any)?.numero_conselho || '',
        uf_conselho: (initialData as any)?.uf_conselho || 'SP',
        codigo_cbo: (initialData as any)?.codigo_cbo || '',
    });

    const [errors, setErrors] = useState<Record<string, string>>({});
    const [submitting, setSubmitting] = useState(false);

    // CBO search state
    const [cboSearch, setCboSearch] = useState('');
    const [cboResults, setCboResults] = useState<CBOOcupacao[]>([]);
    const [cboLoading, setCboLoading] = useState(false);
    const [showCboDropdown, setShowCboDropdown] = useState(false);
    const [selectedCbo, setSelectedCbo] = useState<CBOOcupacao | null>(null);

    // Load CBO if editing
    useEffect(() => {
        if ((initialData as any)?.codigo_cbo) {
            loadCboDetails((initialData as any).codigo_cbo);
        }
    }, [initialData]);

    const loadCboDetails = async (codigo: string) => {
        try {
            const res = await axios.get(`${API_URL}/cbo/${codigo}/`);
            setSelectedCbo(res.data);
        } catch (err) {
            console.error('Erro ao carregar CBO:', err);
        }
    };

    const searchCbo = async (term: string) => {
        if (term.length < 2) {
            setCboResults([]);
            return;
        }

        setCboLoading(true);
        try {
            const res = await axios.get(`${API_URL}/cbo/search/?q=${encodeURIComponent(term)}`);
            setCboResults(res.data.results || []);
            setShowCboDropdown(true);
        } catch (err) {
            console.error('Erro na busca CBO:', err);
        } finally {
            setCboLoading(false);
        }
    };

    const loadCboByFamily = async (familia: string) => {
        setCboLoading(true);
        try {
            const res = await axios.get(`${API_URL}/cbo/search/?family=${familia}`);
            setCboResults(res.data.results || []);
            setShowCboDropdown(true);
        } catch (err) {
            console.error('Erro ao carregar CBO:', err);
        } finally {
            setCboLoading(false);
        }
    };

    const selectCbo = (ocupacao: CBOOcupacao) => {
        setSelectedCbo(ocupacao);
        setFormData({
            ...formData,
            codigo_cbo: ocupacao.codigo,
            qualification_display: ocupacao.nome
        } as any);
        setCboSearch('');
        setShowCboDropdown(false);
    };

    const clearCbo = () => {
        setSelectedCbo(null);
        setFormData({ ...formData, codigo_cbo: '', qualification_display: '' } as any);
    };

    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!formData.family_name.trim()) {
            newErrors.family_name = 'Sobrenome é obrigatório';
        }

        if (!formData.given_names[0]?.trim()) {
            newErrors.given_names = 'Nome é obrigatório';
        }

        if (!(formData as any).numero_conselho?.trim()) {
            newErrors.numero_conselho = 'Número do conselho é obrigatório';
        }

        if (!(formData as any).codigo_cbo?.trim()) {
            newErrors.codigo_cbo = 'Selecione uma ocupação/especialidade CBO';
        }

        if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'Email inválido';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit(formData);
        } catch (error) {
            console.error('Error submitting form:', error);
        } finally {
            setSubmitting(false);
        }
    };

    const inputStyle: React.CSSProperties = {
        width: '100%',
        padding: spacing.sm,
        border: `1px solid ${colors.border.light}`,
        borderRadius: borderRadius.md,
        fontSize: '1rem',
        fontFamily: 'inherit',
    };

    const labelStyle: React.CSSProperties = {
        display: 'block',
        marginBottom: spacing.xs,
        fontWeight: 500,
        color: colors.text.primary,
    };

    const errorStyle: React.CSSProperties = {
        color: colors.alert.critical,
        fontSize: '0.85rem',
        marginTop: spacing.xs,
    };

    const UF_OPTIONS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'];

    return (
        <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
            {/* Prefix */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Prefixo (opcional)</label>
                <select
                    value={formData.prefix}
                    onChange={(e) => setFormData({ ...formData, prefix: e.target.value })}
                    style={inputStyle}
                    aria-label="Prefixo do nome"
                >
                    <option value="">Selecione...</option>
                    <option value="Dr.">Dr.</option>
                    <option value="Dra.">Dra.</option>
                    <option value="Enf.">Enf.</option>
                    <option value="Enfa.">Enfa.</option>
                    <option value="Prof.">Prof.</option>
                    <option value="Profa.">Profa.</option>
                </select>
            </div>

            {/* Given Names */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Nome *</label>
                <input
                    type="text"
                    value={formData.given_names[0] || ''}
                    onChange={(e) => setFormData({ ...formData, given_names: [e.target.value] })}
                    style={inputStyle}
                    placeholder="Ex: Maria da Silva"
                />
                {errors.given_names && <div style={errorStyle}>{errors.given_names}</div>}
            </div>

            {/* Family Name */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Sobrenome *</label>
                <input
                    type="text"
                    value={formData.family_name}
                    onChange={(e) => setFormData({ ...formData, family_name: e.target.value })}
                    style={inputStyle}
                    placeholder="Ex: Santos"
                />
                {errors.family_name && <div style={errorStyle}>{errors.family_name}</div>}
            </div>

            {/* Conselho Profissional */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Conselho Profissional *</label>
                <div style={{ display: 'flex', gap: spacing.sm }}>
                    <select
                        value={(formData as any).conselho || 'CRM'}
                        onChange={(e) => setFormData({ ...formData, conselho: e.target.value } as any)}
                        style={{ ...inputStyle, flex: '0 0 120px' }}
                        aria-label="Tipo de conselho profissional"
                    >
                        <option value="CRM">CRM</option>
                        <option value="COREN">COREN</option>
                        <option value="CRO">CRO</option>
                        <option value="CRF">CRF</option>
                        <option value="CREFITO">CREFITO</option>
                        <option value="CRN">CRN</option>
                        <option value="CRFa">CRFa</option>
                        <option value="CRP">CRP</option>
                        <option value="CRBM">CRBM</option>
                        <option value="CRESS">CRESS</option>
                    </select>
                    <input
                        type="text"
                        value={(formData as any).numero_conselho || ''}
                        onChange={(e) => setFormData({ ...formData, numero_conselho: e.target.value } as any)}
                        style={{ ...inputStyle, flex: 1 }}
                        placeholder="Número (ex: 123456)"
                    />
                    <select
                        value={(formData as any).uf_conselho || 'SP'}
                        onChange={(e) => setFormData({ ...formData, uf_conselho: e.target.value } as any)}
                        style={{ ...inputStyle, flex: '0 0 80px' }}
                        aria-label="UF do conselho"
                    >
                        {UF_OPTIONS.map(uf => (
                            <option key={uf} value={uf}>{uf}</option>
                        ))}
                    </select>
                </div>
                {errors.numero_conselho && <div style={errorStyle}>{errors.numero_conselho}</div>}
            </div>

            {/* CBO - Ocupação/Especialidade */}
            <div style={{ marginBottom: spacing.md, position: 'relative' }}>
                <label style={labelStyle}>Ocupação/Especialidade (CBO) *</label>

                {selectedCbo ? (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: spacing.sm,
                        background: colors.primary.light || '#e0f2fe',
                        border: `1px solid ${colors.primary.medium}`,
                        borderRadius: borderRadius.md,
                    }}>
                        <div>
                            <div style={{ fontWeight: 600, color: colors.primary.medium, fontSize: '0.85rem' }}>
                                {selectedCbo.codigo}
                            </div>
                            <div style={{ fontWeight: 500 }}>{selectedCbo.nome}</div>
                            <div style={{ fontSize: '0.75rem', color: colors.text.secondary }}>
                                {selectedCbo.familia_nome}
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={clearCbo}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.5rem',
                                cursor: 'pointer',
                                color: colors.text.secondary,
                            }}
                            aria-label="Limpar seleção CBO"
                        >
                            ×
                        </button>
                    </div>
                ) : (
                    <>
                        <input
                            type="text"
                            value={cboSearch}
                            onChange={(e) => {
                                setCboSearch(e.target.value);
                                searchCbo(e.target.value);
                            }}
                            style={inputStyle}
                            placeholder="Digite para buscar ocupação..."
                            onFocus={() => cboResults.length > 0 && setShowCboDropdown(true)}
                        />

                        {/* Quick access buttons */}
                        <div style={{ display: 'flex', gap: spacing.xs, marginTop: spacing.xs, flexWrap: 'wrap' }}>
                            <button type="button" onClick={() => loadCboByFamily('2251')}
                                style={{ padding: '4px 8px', borderRadius: '12px', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontSize: '0.75rem' }}>
                                👨‍⚕️ Médicos
                            </button>
                            <button type="button" onClick={() => loadCboByFamily('2235')}
                                style={{ padding: '4px 8px', borderRadius: '12px', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontSize: '0.75rem' }}>
                                👩‍⚕️ Enfermeiros
                            </button>
                            <button type="button" onClick={() => loadCboByFamily('2232')}
                                style={{ padding: '4px 8px', borderRadius: '12px', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontSize: '0.75rem' }}>
                                🦷 Dentistas
                            </button>
                            <button type="button" onClick={() => loadCboByFamily('2236')}
                                style={{ padding: '4px 8px', borderRadius: '12px', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontSize: '0.75rem' }}>
                                🏃 Fisioterapeutas
                            </button>
                            <button type="button" onClick={() => loadCboByFamily('2515')}
                                style={{ padding: '4px 8px', borderRadius: '12px', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontSize: '0.75rem' }}>
                                🧠 Psicólogos
                            </button>
                        </div>

                        {/* Dropdown */}
                        {showCboDropdown && cboResults.length > 0 && (
                            <ul style={{
                                position: 'absolute',
                                top: '100%',
                                left: 0,
                                right: 0,
                                maxHeight: '250px',
                                overflowY: 'auto',
                                background: 'white',
                                border: `1px solid ${colors.border.light}`,
                                borderRadius: borderRadius.md,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                                listStyle: 'none',
                                padding: 0,
                                margin: '4px 0 0',
                                zIndex: 100,
                            }}>
                                {cboResults.map(ocupacao => (
                                    <li
                                        key={ocupacao.codigo}
                                        onClick={() => selectCbo(ocupacao)}
                                        style={{
                                            display: 'flex',
                                            gap: spacing.sm,
                                            padding: spacing.sm,
                                            cursor: 'pointer',
                                            borderBottom: `1px solid ${colors.border.light}`,
                                        }}
                                        onMouseEnter={(e) => e.currentTarget.style.background = colors.background.muted || '#f9fafb'}
                                        onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                                    >
                                        <span style={{
                                            background: colors.primary.medium,
                                            color: 'white',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            fontSize: '0.75rem',
                                            fontWeight: 600,
                                            whiteSpace: 'nowrap',
                                            height: 'fit-content',
                                        }}>
                                            {ocupacao.codigo}
                                        </span>
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{ocupacao.nome}</div>
                                            <div style={{ fontSize: '0.75rem', color: colors.text.secondary }}>
                                                {ocupacao.descricao}
                                            </div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </>
                )}

                {errors.codigo_cbo && <div style={errorStyle}>{errors.codigo_cbo}</div>}
            </div>

            {/* Gender */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Gênero</label>
                <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value as any })}
                    style={inputStyle}
                    aria-label="Gênero"
                >
                    <option value="male">Masculino</option>
                    <option value="female">Feminino</option>
                    <option value="other">Outro</option>
                    <option value="unknown">Não informado</option>
                </select>
            </div>

            {/* Birth Date */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Data de Nascimento</label>
                <input
                    type="date"
                    value={formData.birthDate}
                    onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
                    style={inputStyle}
                />
            </div>

            {/* Phone */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Telefone</label>
                <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    style={inputStyle}
                    placeholder="(11) 98765-4321"
                />
            </div>

            {/* Email */}
            <div style={{ marginBottom: spacing.md }}>
                <label style={labelStyle}>Email</label>
                <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    style={inputStyle}
                    placeholder="exemplo@hospital.com"
                />
                {errors.email && <div style={errorStyle}>{errors.email}</div>}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: spacing.md, marginTop: spacing.lg }}>
                <Button
                    type="submit"
                    disabled={submitting}
                    style={{ flex: 1 }}
                >
                    {submitting ? 'Salvando...' : 'Salvar Profissional'}
                </Button>
                <Button
                    type="button"
                    variant="secondary"
                    onClick={onCancel}
                    disabled={submitting}
                    style={{ flex: 1 }}
                >
                    Cancelar
                </Button>
            </div>
        </form>
    );
};

export default PractitionerForm;

