/**
 * Prescription Workspace - e-Prescribing Frontend
 * 
 * Prescrição eletrônica com:
 * - Busca de medicamentos
 * - Validação ANVISA para controlados
 * - Lista de prescrições
 * - Assinatura digital (placeholder)
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search, Plus, Trash2, AlertTriangle, FileText, Pill, CheckCircle } from 'lucide-react';
import { useIsMobile } from '../../hooks/useMediaQuery';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Drug {
    code: string;
    name: string;
    presentation: string;
    class: string;
    controlled: boolean;
    anvisa_class?: string;
}

interface PrescriptionItem {
    drug: Drug;
    dosage: string;
    frequency: string;
    duration: string;
    quantity: number;
    instructions: string;
}

interface PrescriptionWorkspaceProps {
    patientId?: string;
    patientName?: string;
}

const PrescriptionWorkspace: React.FC<PrescriptionWorkspaceProps> = ({
    patientId = '',
    patientName = 'Paciente'
}) => {
    const isMobile = useIsMobile();
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Drug[]>([]);
    const [prescriptionItems, setPrescriptionItems] = useState<PrescriptionItem[]>([]);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);

    // Current item being added
    const [selectedDrug, setSelectedDrug] = useState<Drug | null>(null);
    const [dosage, setDosage] = useState('');
    const [frequency, setFrequency] = useState('');
    const [duration, setDuration] = useState('');
    const [quantity, setQuantity] = useState(1);
    const [instructions, setInstructions] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const searchDrugs = useCallback(async (query: string) => {
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }

        setLoading(true);
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/prescriptions/drugs/`, {
                params: { q: query },
                headers
            });
            setSearchResults(response.data.results || []);
        } catch (error) {
            console.error('Error searching drugs:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const timeout = setTimeout(() => {
            if (searchQuery) {
                searchDrugs(searchQuery);
            }
        }, 300);
        return () => clearTimeout(timeout);
    }, [searchQuery, searchDrugs]);

    const selectDrug = (drug: Drug) => {
        setSelectedDrug(drug);
        setSearchQuery('');
        setSearchResults([]);
    };

    const addItemToPrescription = () => {
        if (!selectedDrug || !dosage || !frequency || !duration) {
            alert('Preencha todos os campos obrigatórios');
            return;
        }

        const newItem: PrescriptionItem = {
            drug: selectedDrug,
            dosage,
            frequency,
            duration,
            quantity,
            instructions
        };

        setPrescriptionItems([...prescriptionItems, newItem]);

        // Reset form
        setSelectedDrug(null);
        setDosage('');
        setFrequency('');
        setDuration('');
        setQuantity(1);
        setInstructions('');
    };

    const removeItem = (index: number) => {
        setPrescriptionItems(prescriptionItems.filter((_, i) => i !== index));
    };

    const submitPrescription = async () => {
        if (prescriptionItems.length === 0) {
            alert('Adicione pelo menos um medicamento');
            return;
        }

        if (!patientId) {
            alert('Selecione um paciente');
            return;
        }

        setSubmitting(true);
        try {
            const headers = getAuthHeaders();
            const data = {
                patient_id: patientId,
                items: prescriptionItems.map(item => ({
                    drug_code: item.drug.code,
                    dosage: item.dosage,
                    frequency: item.frequency,
                    duration: item.duration,
                    quantity: item.quantity,
                    instructions: item.instructions
                })),
                notes
            };

            const response = await axios.post(`${API_URL}/prescriptions/`, data, { headers });

            if (response.data.success) {
                setSuccess(true);
                setPrescriptionItems([]);
                setNotes('');
                setTimeout(() => setSuccess(false), 3000);
            }
        } catch (error) {
            console.error('Error creating prescription:', error);
            alert('Erro ao criar prescrição');
        } finally {
            setSubmitting(false);
        }
    };

    const hasControlledDrugs = prescriptionItems.some(item => item.drug.controlled);

    return (
        <div style={{ padding: isMobile ? '1rem' : '1.5rem' }}>
            {/* Header */}
            <div style={{ marginBottom: '1.5rem' }}>
                <h1 style={{ margin: 0, fontSize: isMobile ? '1.25rem' : '1.5rem', color: '#1e3a5f', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Pill size={isMobile ? 24 : 28} />
                    Prescrição Eletrônica
                </h1>
                <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: isMobile ? '0.875rem' : '1rem' }}>
                    Paciente: <strong>{patientName || 'Não selecionado'}</strong>
                </p>
            </div>

            {/* Success Message */}
            {success && (
                <div style={{
                    padding: '1rem',
                    background: '#d1fae5',
                    borderRadius: '8px',
                    marginBottom: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    color: '#065f46'
                }}>
                    <CheckCircle size={20} />
                    <strong>Prescrição criada com sucesso!</strong>
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: '1.5rem' }}>
                {/* Left Column - Drug Search & Form */}
                <div style={{ background: 'white', borderRadius: '12px', padding: isMobile ? '1rem' : '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', flex: 1 }}>
                    <h2 style={{ margin: '0 0 1rem 0', fontSize: isMobile ? '1rem' : '1.1rem', color: '#1e3a5f' }}>
                        Adicionar Medicamento
                    </h2>

                    {/* Drug Search */}
                    <div style={{ position: 'relative', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
                            <Search size={18} color="#94a3b8" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Buscar medicamento..."
                                style={{
                                    flex: 1,
                                    border: 'none',
                                    outline: 'none',
                                    fontSize: isMobile ? '16px' : '0.95rem'
                                }}
                            />
                            {loading && <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Buscando...</span>}
                        </div>

                        {/* Search Results Dropdown */}
                        {searchResults.length > 0 && (
                            <div style={{
                                position: 'absolute',
                                top: '100%',
                                left: 0,
                                right: 0,
                                background: 'white',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                                maxHeight: '300px',
                                overflow: 'auto',
                                zIndex: 100
                            }}>
                                {searchResults.map((drug) => (
                                    <div
                                        key={drug.code}
                                        onClick={() => selectDrug(drug)}
                                        style={{
                                            padding: '0.75rem 1rem',
                                            cursor: 'pointer',
                                            borderBottom: '1px solid #f1f5f9',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center'
                                        }}
                                        onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                                        onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                                    >
                                        <div>
                                            <div style={{ fontWeight: '500' }}>{drug.name}</div>
                                            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{drug.presentation} - {drug.class}</div>
                                        </div>
                                        {drug.controlled && (
                                            <span style={{
                                                padding: '0.25rem 0.5rem',
                                                background: '#fef3c7',
                                                color: '#92400e',
                                                borderRadius: '4px',
                                                fontSize: '0.7rem',
                                                fontWeight: '600'
                                            }}>
                                                {drug.anvisa_class || 'Controlado'}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Selected Drug */}
                    {selectedDrug && (
                        <div style={{
                            padding: '1rem',
                            background: '#f0f9ff',
                            borderRadius: '8px',
                            marginBottom: '1rem',
                            border: '1px solid #bae6fd'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <strong>{selectedDrug.name}</strong>
                                    <span style={{ marginLeft: '0.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                                        ({selectedDrug.presentation})
                                    </span>
                                </div>
                                {selectedDrug.controlled && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#d97706' }}>
                                        <AlertTriangle size={16} />
                                        <span style={{ fontSize: '0.8rem', fontWeight: '600' }}>
                                            Receita {selectedDrug.anvisa_class}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Prescription Form */}
                    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                                Posologia *
                            </label>
                            <input
                                type="text"
                                value={dosage}
                                onChange={(e) => setDosage(e.target.value)}
                                placeholder="Ex: 500mg"
                                style={inputStyle}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                                Frequência *
                            </label>
                            <select value={frequency} onChange={(e) => setFrequency(e.target.value)} style={inputStyle}>
                                <option value="">Selecione...</option>
                                <option value="1x/dia">1x ao dia</option>
                                <option value="2x/dia">2x ao dia (12/12h)</option>
                                <option value="3x/dia">3x ao dia (8/8h)</option>
                                <option value="4x/dia">4x ao dia (6/6h)</option>
                                <option value="SOS">Se necessário (SOS)</option>
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                                Duração *
                            </label>
                            <select value={duration} onChange={(e) => setDuration(e.target.value)} style={inputStyle}>
                                <option value="">Selecione...</option>
                                <option value="3 dias">3 dias</option>
                                <option value="5 dias">5 dias</option>
                                <option value="7 dias">7 dias</option>
                                <option value="10 dias">10 dias</option>
                                <option value="14 dias">14 dias</option>
                                <option value="30 dias">30 dias</option>
                                <option value="Uso contínuo">Uso contínuo</option>
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                                Quantidade
                            </label>
                            <input
                                type="number"
                                value={quantity}
                                onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                                min={1}
                                style={inputStyle}
                            />
                        </div>
                    </div>

                    <div style={{ marginTop: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                            Instruções adicionais
                        </label>
                        <textarea
                            value={instructions}
                            onChange={(e) => setInstructions(e.target.value)}
                            placeholder="Ex: Tomar com água, após as refeições"
                            rows={2}
                            style={{ ...inputStyle, resize: 'vertical' }}
                        />
                    </div>

                    <button
                        onClick={addItemToPrescription}
                        disabled={!selectedDrug}
                        style={{
                            marginTop: '1rem',
                            width: '100%',
                            padding: '0.75rem',
                            background: selectedDrug ? '#3b82f6' : '#e5e7eb',
                            color: selectedDrug ? 'white' : '#94a3b8',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: selectedDrug ? 'pointer' : 'not-allowed',
                            fontWeight: '600',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <Plus size={18} />
                        Adicionar à Prescrição
                    </button>
                </div>

                {/* Right Column - Prescription Preview */}
                <div style={{ background: 'white', borderRadius: '12px', padding: isMobile ? '1rem' : '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', flex: 1 }}>
                    <h2 style={{ margin: '0 0 1rem 0', fontSize: isMobile ? '1rem' : '1.1rem', color: '#1e3a5f', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        <FileText size={20} />
                        Receita
                        {hasControlledDrugs && (
                            <span style={{
                                marginLeft: 'auto',
                                padding: '0.25rem 0.75rem',
                                background: '#fef3c7',
                                color: '#92400e',
                                borderRadius: '9999px',
                                fontSize: '0.75rem',
                                fontWeight: '600'
                            }}>
                                ⚠️ Contém Controlados
                            </span>
                        )}
                    </h2>

                    {prescriptionItems.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
                            <Pill size={48} style={{ marginBottom: '1rem', opacity: 0.3 }} />
                            <p>Nenhum medicamento adicionado</p>
                            <p style={{ fontSize: '0.85rem' }}>Busque e adicione medicamentos à prescrição</p>
                        </div>
                    ) : (
                        <>
                            <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                                {prescriptionItems.map((item, index) => (
                                    <div
                                        key={index}
                                        style={{
                                            padding: '1rem',
                                            background: item.drug.controlled ? '#fffbeb' : '#f8fafc',
                                            borderRadius: '8px',
                                            marginBottom: '0.75rem',
                                            border: item.drug.controlled ? '1px solid #fcd34d' : '1px solid #e5e7eb'
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                            <div>
                                                <div style={{ fontWeight: '600', color: '#1e3a5f', marginBottom: '0.25rem' }}>
                                                    {index + 1}. {item.drug.name}
                                                    {item.drug.controlled && (
                                                        <span style={{
                                                            marginLeft: '0.5rem',
                                                            padding: '0.125rem 0.375rem',
                                                            background: '#fcd34d',
                                                            color: '#78350f',
                                                            borderRadius: '4px',
                                                            fontSize: '0.65rem',
                                                            fontWeight: '700'
                                                        }}>
                                                            {item.drug.anvisa_class}
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                                                    {item.dosage} - {item.frequency} por {item.duration}
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                                                    Quantidade: {item.quantity} | {item.instructions || 'Sem instruções adicionais'}
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeItem(index)}
                                                style={{
                                                    background: 'none',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    color: '#ef4444',
                                                    padding: '0.25rem'
                                                }}
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Notes */}
                            <div style={{ marginTop: '1rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                                    Observações Clínicas
                                </label>
                                <textarea
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    placeholder="Observações adicionais para o farmacêutico..."
                                    rows={3}
                                    style={{ ...inputStyle, resize: 'vertical' }}
                                />
                            </div>

                            {/* Submit */}
                            <button
                                onClick={submitPrescription}
                                disabled={submitting || !patientId}
                                style={{
                                    marginTop: '1rem',
                                    width: '100%',
                                    padding: '1rem',
                                    background: submitting ? '#94a3b8' : '#10b981',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: submitting ? 'not-allowed' : 'pointer',
                                    fontWeight: '600',
                                    fontSize: '1rem'
                                }}
                            >
                                {submitting ? '⏳ Processando...' : '✅ Finalizar Prescrição'}
                            </button>

                            {hasControlledDrugs && (
                                <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#92400e', textAlign: 'center' }}>
                                    ⚠️ Esta receita contém medicamentos controlados e requer assinatura digital.
                                </p>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '0.9rem',
    outline: 'none',
    boxSizing: 'border-box'
};

export default PrescriptionWorkspace;
