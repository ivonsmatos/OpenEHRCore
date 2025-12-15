import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePatients } from '../../hooks/usePatients';
import { useEncounters } from '../../hooks/useEncounters';
import { useIsMobile, useIsTabletOrBelow } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import Card from '../base/Card';
import { colors, spacing } from '../../theme/colors';
import { getPatientSummary } from '../../utils/fhirParser';
import './ClinicalWorkspace.css';

import VitalSignsForm from './VitalSignsForm';
import ConditionForm from './ConditionForm';
import AllergyForm from './AllergyForm';
import PrescriptionForm from './PrescriptionForm';
import ExamForm from './ExamForm';
import SOAPNote from './SOAPNote';
import ImmunizationForm from './ImmunizationForm';

type Tab = 'vitals' | 'soap' | 'conditions' | 'allergies' | 'prescriptions' | 'exams' | 'immunizations';

const NavButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode; icon: string }> = ({ active, onClick, children, icon }) => (
    <button
        onClick={onClick}
        style={{
            display: 'flex',
            alignItems: 'center',
            gap: spacing.sm,
            width: '100%',
            padding: spacing.md,
            border: 'none',
            borderRadius: '8px',
            backgroundColor: active ? 'white' : 'transparent',
            color: active ? colors.primary.dark : colors.text.secondary,
            fontWeight: active ? 600 : 400,
            cursor: 'pointer',
            textAlign: 'left',
            boxShadow: active ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
            transition: 'all 0.2s ease'
        }}
    >
        <span>{icon}</span>
        {children}
    </button>
);

export const ClinicalWorkspace: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { getPatient } = usePatients();
    const { createEncounter } = useEncounters(id); // Passar o patientId aqui
    const isMobile = useIsMobile();
    const isTabletOrBelow = useIsTabletOrBelow();

    const [patient, setPatient] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<Tab>('soap');
    const [encounterId, setEncounterId] = useState<string | null>(null);

    useEffect(() => {
        const initWorkspace = async () => {
            if (!id) return;
            try {
                // 1. Fetch Patient
                const patientData = await getPatient(id);
                setPatient(patientData);

                // 2. Auto-start encounter if new
                try {
                    const newEncounter = await createEncounter({
                        status: 'in-progress',
                        reasonCode: [{
                            text: 'Atendimento Clínico'
                        }],
                        period: {
                            start: new Date().toISOString()
                        }
                    });

                    if (newEncounter && newEncounter.id) {
                        setEncounterId(newEncounter.id);
                    }
                } catch (encounterError) {
                    console.warn("Could not auto-create encounter. Workspace will continue without encounter ID:", encounterError);
                    // Workspace continua funcionando mesmo sem encounter
                    setEncounterId(null);
                }

            } catch (error) {
                console.error("Error initializing workspace:", error);
                // Erro crítico apenas se não conseguir carregar o paciente
            } finally {
                setLoading(false);
            }
        };

        initWorkspace();
    }, [id]);

    const handleFinishEncounter = async () => {
        // Logic to update encounter status to 'finished'
        // For now, just navigate back
        navigate(`/patients/${id}`);
    };

    if (loading) {
        return <div style={{ padding: spacing.xl, textAlign: 'center' }}>Carregando Workspace Clínico...</div>;
    }

    if (!patient) {
        return <div style={{ padding: spacing.xl, color: colors.alert.critical }}>Paciente não encontrado.</div>;
    }

    const summary = getPatientSummary(patient);

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: colors.background.surface }}>
            {/* Compact Header */}
            <header style={{
                padding: isMobile ? spacing.sm : `${spacing.sm} ${spacing.lg}`,
                borderBottom: `1px solid ${colors.border.light}`,
                backgroundColor: 'white',
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: isMobile ? spacing.sm : '0'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, width: isMobile ? '100%' : 'auto' }}>
                    <div style={{
                        width: isMobile ? '36px' : '40px',
                        height: isMobile ? '36px' : '40px',
                        borderRadius: '50%',
                        backgroundColor: colors.primary.light,
                        color: colors.primary.dark,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: isMobile ? '0.9rem' : '1rem',
                        flexShrink: 0
                    }}>
                        {summary.initials}
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                        <h1 style={{ fontSize: isMobile ? '1rem' : '1.125rem', margin: 0, color: colors.text.primary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{summary.name}</h1>
                        <span style={{ fontSize: isMobile ? '0.8rem' : '0.875rem', color: colors.text.secondary }}>
                            {summary.age} anos • {summary.gender}
                        </span>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: spacing.sm, width: isMobile ? '100%' : 'auto', flexWrap: isMobile ? 'wrap' : 'nowrap' }}>
                    <div style={{
                        padding: `${spacing.xs} ${isMobile ? spacing.sm : spacing.md}`,
                        backgroundColor: colors.alert.warning,
                        color: 'white',
                        borderRadius: '16px',
                        fontSize: isMobile ? '0.7rem' : '0.75rem',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        whiteSpace: 'nowrap'
                    }}>
                        EM ATENDIMENTO
                    </div>
                    <Button variant="primary" onClick={handleFinishEncounter} style={{ fontSize: isMobile ? '0.85rem' : '1rem' }}>
                        {isMobile ? 'Finalizar' : 'Finalizar Atendimento'}
                    </Button>
                </div>
            </header>

            {/* Main Content Area */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', flexDirection: isMobile ? 'column' : 'row' }}>
                {/* Sidebar Navigation - Tabs horizontais no mobile */}
                {isMobile ? (
                    <nav 
                        className="clinical-tabs-nav"
                        style={{
                            backgroundColor: 'white',
                            borderBottom: `1px solid ${colors.border.light}`,
                            padding: `${spacing.sm} ${spacing.xs}`,
                            overflowX: 'auto',
                            whiteSpace: 'nowrap',
                            WebkitOverflowScrolling: 'touch'
                        }}
                    >
                        <div style={{ display: 'flex', gap: spacing.sm }}>
                            {[
                                { id: 'soap', label: 'SOAP', icon: '📝' },
                                { id: 'vitals', label: 'Vitais', icon: '🩺' },
                                { id: 'conditions', label: 'Diagnósticos', icon: '⚠️' },
                                { id: 'allergies', label: 'Alergias', icon: '🚫' },
                                { id: 'immunizations', label: 'Vacinas', icon: '💉' },
                                { id: 'prescriptions', label: 'Prescrição', icon: '💊' },
                                { id: 'exams', label: 'Exames', icon: '🔬' }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as Tab)}
                                    className="clinical-tab-button"
                                    style={{
                                        display: 'inline-flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '2px',
                                        padding: `${spacing.xs} 10px`,
                                        minWidth: '70px',
                                        border: 'none',
                                        borderRadius: '8px',
                                        backgroundColor: activeTab === tab.id ? colors.primary.light : 'transparent',
                                        color: activeTab === tab.id ? colors.primary.dark : colors.text.secondary,
                                        fontSize: '0.7rem',
                                        fontWeight: activeTab === tab.id ? 600 : 400,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                        whiteSpace: 'nowrap',
                                        lineHeight: '1.1'
                                    }}
                                >
                                    <span style={{ fontSize: '1.1rem' }}>{tab.icon}</span>
                                    <span style={{ maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tab.label}</span>
                                </button>
                            ))}
                        </div>
                    </nav>
                ) : (
                    <nav style={{
                        width: isTabletOrBelow ? '180px' : '240px',
                        backgroundColor: colors.background.muted,
                        borderRight: `1px solid ${colors.border.light}`,
                        padding: spacing.md,
                        overflowY: 'auto'
                    }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.xs }}>
                            <NavButton active={activeTab === 'soap'} onClick={() => setActiveTab('soap')} icon="📝">
                                Notas (SOAP)
                            </NavButton>
                            <NavButton active={activeTab === 'vitals'} onClick={() => setActiveTab('vitals')} icon="🩺">
                                Sinais Vitais
                            </NavButton>
                            <NavButton active={activeTab === 'conditions'} onClick={() => setActiveTab('conditions')} icon="⚠️">
                                Diagnósticos
                            </NavButton>
                            <NavButton active={activeTab === 'allergies'} onClick={() => setActiveTab('allergies')} icon="🚫">
                                Alergias
                            </NavButton>
                            <NavButton active={activeTab === 'immunizations'} onClick={() => setActiveTab('immunizations')} icon="💉">
                                Vacinas
                            </NavButton>
                            <NavButton active={activeTab === 'prescriptions'} onClick={() => setActiveTab('prescriptions')} icon="💊">
                                Prescrição
                            </NavButton>
                            <NavButton active={activeTab === 'exams'} onClick={() => setActiveTab('exams')} icon="🔬">
                                Exames
                            </NavButton>
                        </div>
                    </nav>
                )}

                {/* Active Form Area */}
                <main style={{ flex: 1, padding: isMobile ? spacing.md : (isTabletOrBelow ? spacing.lg : spacing.xl), overflowY: 'auto' }}>
                    <Card padding={isMobile ? "md" : "lg"}>
                        {activeTab === 'soap' && <SOAPNote patientId={id} encounterId={encounterId} />}
                        {activeTab === 'vitals' && <VitalSignsForm patientId={id} encounterId={encounterId} />}
                        {activeTab === 'conditions' && <ConditionForm patientId={id} encounterId={encounterId} />}
                        {activeTab === 'allergies' && <AllergyForm patientId={id} encounterId={encounterId} />}
                        {activeTab === 'immunizations' && <ImmunizationForm patientId={id} encounterId={encounterId} />}
                        {activeTab === 'prescriptions' && <PrescriptionForm patientId={id} encounterId={encounterId} />}
                        {activeTab === 'exams' && <ExamForm patientId={id} encounterId={encounterId} />}
                    </Card>
                </main>
            </div>
        </div>
    );
};

export default ClinicalWorkspace;
