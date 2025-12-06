
import React, { useEffect, useState } from 'react';
import Card from '../base/Card';
import { colors, spacing, borderRadius, typography } from '../../theme/colors';
import { User, Activity, AlertCircle, Calendar, HeartPulse } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const API_BASE = 'http://localhost:8000/api/v1';

interface BedDetailsModalProps {
    locationId: string;
    onClose: () => void;
    onAdmit: () => void; // Callback to switch to admission mode
}

interface ClinicalSummary {
    conditions: any[];
    observations: any[];
}

interface BedDetails {
    location: any;
    status_code: string;
    patient: any | null;
    encounter: any | null;
    clinical_summary: ClinicalSummary;
}

const BedDetailsModal: React.FC<BedDetailsModalProps> = ({ locationId, onClose, onAdmit }) => {
    const { token } = useAuth();
    const [details, setDetails] = useState<BedDetails | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDetails();
    }, [locationId]);

    const fetchDetails = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/ipd/bed/${locationId}/details/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDetails(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDischarge = async () => {
        if (!confirm("Tem certeza que deseja dar alta a este paciente? O leito será marcado para higienização.")) return;

        try {
            const res = await fetch(`${API_BASE}/ipd/discharge/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ location_id: locationId })
            });

            if (res.ok) {
                alert("Alta realizada. Leito em higienização.");
                onClose();
                window.location.reload();
            } else {
                const err = await res.json();
                alert(`Erro ao registrar alta: ${err.error || res.statusText}`);
            }
        } catch (error) {
            console.error("Error discharging", error);
            alert("Erro de conexão ao registrar alta.");
        }
    };

    const handleFinishCleaning = async () => {
        try {
            const res = await fetch(`${API_BASE}/ipd/bed/${locationId}/clean/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                alert("Limpeza finalizada. Leito liberado.");
                onClose();
                window.location.reload();
            } else {
                const err = await res.json();
                alert(`Erro ao finalizar limpeza: ${err.error || res.statusText}`);
            }
        } catch (error) { console.error(error); alert("Erro de conexão."); }
    };

    if (loading) return (
        <div style={modalOverlayStyle}>
            <div style={modalContentStyle}>Carregando detalhes...</div>
        </div>
    );

    if (!details) return null;

    const isOccupied = details.status_code === 'O';
    const isCleaning = details.status_code === 'K';

    return (
        <div style={modalOverlayStyle}>
            <div style={modalContentStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md }}>
                    <h2 style={{ margin: 0 }}>{details.location.name}</h2>
                    <button onClick={onClose} style={closeButtonStyle}>✕</button>
                </div>

                <div style={{ marginBottom: spacing.md }}>
                    <span style={{
                        padding: `${spacing.xs} ${spacing.sm}`,
                        backgroundColor: isOccupied ? '#fecaca' : '#d1fae5',
                        color: isOccupied ? '#b91c1c' : '#047857',
                        borderRadius: borderRadius.full,
                        fontWeight: 'bold',
                        fontSize: '0.9rem'
                    }}>
                        {isOccupied ? 'OCUPADO' : 'LIVRE'}
                    </span>
                    <p style={{ color: colors.text.secondary, marginTop: spacing.xs, fontSize: '0.9rem' }}>
                        {details.location.description || 'Sem descrição adicional.'}
                    </p>
                </div>

                {isOccupied && details.patient ? (
                    <>
                        <Card title="Paciente" style={{ marginBottom: spacing.md }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
                                <div style={{
                                    width: 48, height: 48, backgroundColor: colors.primary.light,
                                    borderRadius: borderRadius.full, display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}>
                                    <User color={colors.primary.main} />
                                </div>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
                                        {details.patient.name?.[0]?.text ||
                                            `${details.patient.name?.[0]?.given?.join(' ') || ''} ${details.patient.name?.[0]?.family || ''}`.trim() ||
                                            'Nome Desconhecido'}
                                    </h3>
                                    <p style={{ margin: 0, color: colors.text.secondary, fontSize: '0.9rem' }}>
                                        Nascimento: {details.patient.birthDate} | Sexo: {details.patient.gender}
                                    </p>
                                </div>
                            </div>
                            {details.encounter && (
                                <div style={{ marginTop: spacing.sm, fontSize: '0.85rem', color: colors.text.secondary, display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <Calendar size={14} />
                                    Internado em: {new Date(details.encounter.period?.start).toLocaleString('pt-BR')}
                                </div>
                            )}
                        </Card>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
                            <Card title="Diagnósticos Ativos" style={{ minHeight: 150 }}>
                                {details.clinical_summary.conditions.length > 0 ? (
                                    <ul style={{ paddingLeft: 20, margin: 0 }}>
                                        {details.clinical_summary.conditions.map((c: any) => (
                                            <li key={c.id || Math.random()} style={{ marginBottom: 4 }}>
                                                {c.code?.coding?.[0]?.display || 'Condição sem nome'}
                                                <span style={{ fontSize: '0.8rem', color: colors.text.secondary }}> ({c.clinicalStatus?.coding?.[0]?.code})</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p style={{ color: colors.text.secondary }}>Nenhum diagnóstico registrado.</p>
                                )}
                            </Card>

                            <Card title="Últimos Sinais Vitais" style={{ minHeight: 150 }}>
                                {details.clinical_summary.observations.length > 0 ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
                                        {details.clinical_summary.observations.map((o: any) => {
                                            let val = 'N/A';
                                            if (o.valueQuantity?.value) {
                                                const rawVal = parseFloat(o.valueQuantity.value);
                                                val = `${rawVal.toFixed(1)} ${o.valueQuantity.unit || ''}`;
                                            }
                                            return (
                                                <div key={o.id || Math.random()} style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, padding: spacing.xs, backgroundColor: '#f9fafb', borderRadius: borderRadius.sm }}>
                                                    <HeartPulse size={16} color={colors.primary.main} />
                                                    <div>
                                                        <span style={{ fontWeight: 500 }}>{o.code?.coding?.[0]?.display || 'Sinal'}: </span>
                                                        <span>{val}</span>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                ) : (
                                    <p style={{ color: colors.text.secondary }}>Sem medições recentes.</p>
                                )}
                            </Card>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.md }}>
                            <button
                                onClick={handleDischarge}
                                style={{
                                    padding: `${spacing.sm} ${spacing.md}`,
                                    backgroundColor: '#ef4444',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: borderRadius.md,
                                    cursor: 'pointer',
                                    fontWeight: 'bold',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8
                                }}
                            >
                                <span>Registrar Alta / Liberar Leito</span>
                            </button>
                        </div>
                    </>
                ) : isCleaning ? (
                    <div style={{ textAlign: 'center', padding: spacing.xl }}>
                        <div style={{ marginBottom: spacing.md, color: '#f59e0b' }}>
                            <Activity size={48} />
                        </div>
                        <h3 style={{ color: '#b45309' }}>Leito em Higienização</h3>
                        <p style={{ color: colors.text.secondary, marginBottom: spacing.lg }}>
                            Este leito está aguardando limpeza terminal antes de receber um novo paciente.
                        </p>
                        <button
                            onClick={handleFinishCleaning}
                            style={{
                                padding: `${spacing.md} ${spacing.xl}`,
                                backgroundColor: '#f59e0b',
                                color: 'white',
                                border: 'none',
                                borderRadius: borderRadius.md,
                                fontSize: '1rem',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            Finalizar Limpeza (Liberar Leito)
                        </button>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: spacing.xl, color: colors.text.secondary }}>
                        <p>Este leito está vago e pronto para uso.</p>
                        <button
                            onClick={onAdmit}
                            style={{
                                marginTop: spacing.md,
                                padding: `${spacing.md} ${spacing.xl}`,
                                backgroundColor: colors.primary.medium,
                                color: 'white',
                                border: 'none',
                                borderRadius: borderRadius.md,
                                fontSize: '1rem',
                                cursor: 'pointer'
                            }}
                        >
                            Internar Paciente Neste Leito
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center',
    zIndex: 1000
};

const modalContentStyle: React.CSSProperties = {
    backgroundColor: 'white', padding: spacing.lg, borderRadius: borderRadius.md,
    width: '800px', maxWidth: '90%', maxHeight: '90vh', overflowY: 'auto',
    position: 'relative'
};

const closeButtonStyle: React.CSSProperties = {
    background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: colors.text.secondary
};

export default BedDetailsModal;
