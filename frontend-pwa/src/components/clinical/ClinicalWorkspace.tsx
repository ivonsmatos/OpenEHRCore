import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePatients } from '../../hooks/usePatients';
import { useEncounters } from '../../hooks/useEncounters';
import Button from '../base/Button';
import Card from '../base/Card';
import { colors, spacing } from '../../theme/colors';
import { getPatientSummary } from '../../utils/fhirParser';

import VitalSignsForm from './VitalSignsForm';
import ConditionForm from './ConditionForm';
import AllergyForm from './AllergyForm';
import PrescriptionForm from './PrescriptionForm';
import ExamForm from './ExamForm';
import SOAPNote from './SOAPNote';

type Tab = 'vitals' | 'soap' | 'conditions' | 'allergies' | 'prescriptions' | 'exams';

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
    const { createEncounter } = useEncounters();

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
                // In a real app, we might check if there's already an open encounter for today
                const newEncounter = await createEncounter({
                    patientId: id,
                    status: 'in-progress',
                    type: 'consultation',
                    reason: 'Atendimento Clínico'
                });

                if (newEncounter && newEncounter.id) {
                    setEncounterId(newEncounter.id);
                }

            } catch (error) {
                console.error("Error initializing workspace:", error);
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
                padding: `${spacing.sm} ${spacing.lg}`,
                borderBottom: `1px solid ${colors.border.light}`,
                backgroundColor: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
                    <div style={{
                        width: '40px', height: '40px', borderRadius: '50%',
                        backgroundColor: colors.primary.light, color: colors.primary.dark,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold'
                    }}>
                        {summary.initials}
                    </div>
                    <div>
                        <h1 style={{ fontSize: '1.125rem', margin: 0, color: colors.text.primary }}>{summary.name}</h1>
                        <span style={{ fontSize: '0.875rem', color: colors.text.secondary }}>
                            {summary.age} anos • {summary.gender}
                        </span>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: spacing.sm }}>
                    <div style={{
                        padding: `${spacing.xs} ${spacing.md}`,
                        backgroundColor: colors.alert.warning,
                        color: 'white',
                        borderRadius: '16px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center'
                    }}>
                        EM ATENDIMENTO
                    </div>
                    <Button variant="primary" onClick={handleFinishEncounter}>
                        Finalizar Atendimento
                    </Button>
                </div>
            </header>

            {/* Main Content Area */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                {/* Sidebar Navigation */}
                <nav style={{
                    width: '240px',
                    backgroundColor: colors.background.muted,
                    borderRight: `1px solid ${colors.border.light}`,
                    padding: spacing.md
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
                        <NavButton active={activeTab === 'prescriptions'} onClick={() => setActiveTab('prescriptions')} icon="💊">
                            Prescrição
                        </NavButton>
                        <NavButton active={activeTab === 'exams'} onClick={() => setActiveTab('exams')} icon="🔬">
                            Exames
                        </NavButton>
                    </div>
                </nav>

                {/* Active Form Area */}
                <main style={{ flex: 1, padding: spacing.xl, overflowY: 'auto' }}>
                    <Card padding="lg">
                        {activeTab === 'soap' && <SOAPNote encounterId={encounterId} />}
                        {activeTab === 'vitals' && <VitalSignsForm encounterId={encounterId} />}
                        {activeTab === 'conditions' && <ConditionForm encounterId={encounterId} />}
                        {activeTab === 'allergies' && <AllergyForm encounterId={encounterId} />}
                        {activeTab === 'prescriptions' && <PrescriptionForm encounterId={encounterId} patientId={id} />}
                        {activeTab === 'exams' && <ExamForm encounterId={encounterId} />}
                    </Card>
                </main>
            </div>
        </div>
    );
};

export default ClinicalWorkspace;
