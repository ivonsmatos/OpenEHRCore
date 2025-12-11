import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Pill,
    Clock,
    RefreshCw,
    AlertTriangle,
    Check,
    X,
    ChevronDown,
    Filter
} from 'lucide-react';
import Card from '../base/Card';
import './MedicationHistory.css';

interface MedicationHistoryProps {
    patientId: string;
}

interface MedicationRequest {
    id: string;
    medicationName: string;
    dosage: string;
    frequency: string;
    route: string;
    status: 'active' | 'completed' | 'stopped' | 'on-hold' | 'cancelled';
    authoredOn: string;
    prescriber?: string;
    validityPeriod?: {
        start?: string;
        end?: string;
    };
    notes?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof Check }> = {
    active: { label: 'Ativo', color: '#10b981', icon: Check },
    completed: { label: 'Concluído', color: '#6b7280', icon: Check },
    stopped: { label: 'Parado', color: '#ef4444', icon: X },
    'on-hold': { label: 'Em espera', color: '#f59e0b', icon: Clock },
    cancelled: { label: 'Cancelado', color: '#dc2626', icon: X }
};

/**
 * MedicationHistory - Histórico de medicamentos do paciente
 * 
 * Exibe lista de prescrições com status, dosagem e período de uso
 */
export const MedicationHistory: React.FC<MedicationHistoryProps> = ({ patientId }) => {
    const [medications, setMedications] = useState<MedicationRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [expandedMed, setExpandedMed] = useState<string | null>(null);

    useEffect(() => {
        const fetchMedications = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('access_token');
                const response = await axios.get(
                    `${API_BASE}/patients/${patientId}/medications/`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                // Processar resposta FHIR para formato interno
                const meds = (response.data || []).map((med: any) => ({
                    id: med.id,
                    medicationName: med.medicationCodeableConcept?.coding?.[0]?.display ||
                        med.medicationCodeableConcept?.text ||
                        'Medicamento não especificado',
                    dosage: formatDosage(med.dosageInstruction?.[0]),
                    frequency: formatFrequency(med.dosageInstruction?.[0]?.timing),
                    route: med.dosageInstruction?.[0]?.route?.coding?.[0]?.display || 'Via não especificada',
                    status: med.status || 'active',
                    authoredOn: med.authoredOn || '',
                    prescriber: med.requester?.display || '',
                    validityPeriod: {
                        start: med.dispenseRequest?.validityPeriod?.start,
                        end: med.dispenseRequest?.validityPeriod?.end
                    },
                    notes: med.note?.[0]?.text
                }));

                setMedications(meds);
                setError(null);
            } catch (err) {
                console.error('Erro ao buscar medicamentos:', err);
                setError('Não foi possível carregar histórico de medicamentos');
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchMedications();
        }
    }, [patientId]);

    const formatDosage = (dosage: any): string => {
        if (!dosage) return '-';
        const dose = dosage.doseAndRate?.[0]?.doseQuantity;
        if (dose) {
            return `${dose.value} ${dose.unit || 'unidade(s)'}`;
        }
        return dosage.text || '-';
    };

    const formatFrequency = (timing: any): string => {
        if (!timing) return '-';

        if (timing.code?.coding?.[0]?.display) {
            return timing.code.coding[0].display;
        }

        const repeat = timing.repeat;
        if (repeat) {
            if (repeat.frequency && repeat.period && repeat.periodUnit) {
                const units: Record<string, string> = {
                    h: 'hora(s)',
                    d: 'dia(s)',
                    wk: 'semana(s)',
                    mo: 'mês(es)'
                };
                return `${repeat.frequency}x a cada ${repeat.period} ${units[repeat.periodUnit] || repeat.periodUnit}`;
            }
        }

        return timing.code?.text || '-';
    };

    const formatDate = (dateStr: string): string => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('pt-BR');
    };

    const filteredMedications = medications.filter(med =>
        statusFilter === 'all' || med.status === statusFilter
    );

    const activeMeds = medications.filter(m => m.status === 'active').length;

    if (loading) {
        return (
            <Card className="medication-history-card">
                <div className="mh-loading">
                    <RefreshCw size={32} className="spinning" />
                    <p>Carregando medicamentos...</p>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="medication-history-card">
                <div className="mh-error">
                    <AlertTriangle size={32} />
                    <p>{error}</p>
                </div>
            </Card>
        );
    }

    return (
        <Card className="medication-history-card">
            <div className="mh-header">
                <div className="mh-title">
                    <Pill size={20} />
                    <h3>Histórico de Medicamentos</h3>
                    {activeMeds > 0 && (
                        <span className="active-badge">{activeMeds} ativo{activeMeds > 1 ? 's' : ''}</span>
                    )}
                </div>

                <div className="mh-filter">
                    <Filter size={16} />
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        aria-label="Filtrar por status"
                    >
                        <option value="all">Todos</option>
                        <option value="active">Ativos</option>
                        <option value="completed">Concluídos</option>
                        <option value="stopped">Parados</option>
                    </select>
                    <ChevronDown size={14} />
                </div>
            </div>

            {filteredMedications.length === 0 ? (
                <div className="mh-empty">
                    <Pill size={48} />
                    <p>Nenhum medicamento {statusFilter !== 'all' ? 'neste status' : 'registrado'}</p>
                </div>
            ) : (
                <div className="mh-list">
                    {filteredMedications.map((med) => {
                        const statusInfo = STATUS_CONFIG[med.status] || STATUS_CONFIG.active;
                        const StatusIcon = statusInfo.icon;
                        const isExpanded = expandedMed === med.id;

                        return (
                            <div
                                key={med.id}
                                className={`med-item ${isExpanded ? 'expanded' : ''}`}
                            >
                                <div
                                    className="med-main"
                                    onClick={() => setExpandedMed(isExpanded ? null : med.id)}
                                >
                                    <div className="med-icon" style={{ backgroundColor: `${statusInfo.color}20` }}>
                                        <Pill size={18} style={{ color: statusInfo.color }} />
                                    </div>

                                    <div className="med-info">
                                        <span className="med-name">{med.medicationName}</span>
                                        <span className="med-dosage">{med.dosage} • {med.frequency}</span>
                                    </div>

                                    <div className="med-status" style={{ backgroundColor: `${statusInfo.color}15`, color: statusInfo.color }}>
                                        <StatusIcon size={12} />
                                        {statusInfo.label}
                                    </div>

                                    <ChevronDown
                                        size={18}
                                        className={`med-chevron ${isExpanded ? 'rotated' : ''}`}
                                    />
                                </div>

                                {isExpanded && (
                                    <div className="med-details">
                                        <div className="detail-row">
                                            <span className="detail-label">Via de administração</span>
                                            <span className="detail-value">{med.route}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span className="detail-label">Prescrito em</span>
                                            <span className="detail-value">{formatDate(med.authoredOn)}</span>
                                        </div>
                                        {med.prescriber && (
                                            <div className="detail-row">
                                                <span className="detail-label">Prescritor</span>
                                                <span className="detail-value">{med.prescriber}</span>
                                            </div>
                                        )}
                                        {med.validityPeriod?.end && (
                                            <div className="detail-row">
                                                <span className="detail-label">Válido até</span>
                                                <span className="detail-value">{formatDate(med.validityPeriod.end)}</span>
                                            </div>
                                        )}
                                        {med.notes && (
                                            <div className="detail-row notes">
                                                <span className="detail-label">Observações</span>
                                                <span className="detail-value">{med.notes}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            <div className="mh-footer">
                <span>Total: {medications.length} medicamento{medications.length !== 1 ? 's' : ''}</span>
            </div>
        </Card>
    );
};

export default MedicationHistory;
