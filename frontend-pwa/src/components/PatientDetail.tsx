
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePatients } from "../hooks/usePatients";
import Card from "./base/Card";
import Button from "./base/Button";
import VitalSigns from "./clinical/VitalSigns";
import ProblemList from "./clinical/ProblemList";
import AllergyList from "./clinical/AllergyList";
import EncounterList from "./clinical/EncounterList";
import AppointmentList from "./scheduling/AppointmentList";
import { colors, spacing } from "../theme/colors";
import { Activity } from "lucide-react";
import ClinicalWorkspace from './clinical/ClinicalWorkspace';
import ImmunizationWorkspace from './clinical/ImmunizationWorkspace';
import DiagnosticResultWorkspace from './clinical/DiagnosticResultWorkspace';
import {
  FHIRPatient,
  getPatientSummary,
  isValidPatientResource,
} from "../utils/fhirParser";

interface PatientDetailProps {
  patient?: FHIRPatient;
  loading?: boolean;
  error?: string;
  onEdit?: () => void;
  onDelete?: () => void;
}

/**
 * Componente PatientDetail
 *
 * Exibe informações detalhadas de um paciente com dados estruturados em FHIR.
 * Demonstra:
 * - Parsing seguro de JSON FHIR complexo
 * - Design System com paleta institucional
 * - Whitespace generoso e tipografia moderna
 * - Componentes reutilizáveis (Card, Button, Header)
 */
export const PatientDetail: React.FC<PatientDetailProps> = (props) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { patient, loading: propLoading, error: propError, onEdit } = props;

  // State for view switching
  const [view, setView] = useState<'overview' | 'clinical' | 'immunization' | 'diagnostic'>('overview');

  // Hook para buscar dados
  const { getPatient, deletePatient, loading: hookLoading, error: hookError } = usePatients();

  const [currentPatient, setCurrentPatient] = useState<FHIRPatient | undefined>(patient);

  // Combinar estados de loading e error
  const loading = propLoading || hookLoading;
  const error = propError || hookError;

  useEffect(() => {
    const loadPatientData = async () => {
      if (patient) {
        setCurrentPatient(patient);
      } else if (id) {
        try {
          const fetchedPatient = await getPatient(id);
          setCurrentPatient(fetchedPatient);
        } catch (err) {
          console.error("Erro ao buscar paciente:", err);
        }
      }
    };

    loadPatientData();
  }, [id, patient]);

  const handleDelete = async () => {
    if (!currentPatient?.id) return;
    if (window.confirm("Tem certeza que deseja excluir este paciente? Esta ação não pode ser desfeita.")) {
      try {
        await deletePatient(currentPatient.id);
        navigate('/');
      } catch (err) {
        alert("Erro ao excluir paciente: " + err);
      }
    }
  };

  const handleEdit = () => {
    // Navigate to edit form - passing data via state for now or just navigating
    if (onEdit) {
      onEdit();
    } else {
      // Assuming PatientForm can handle editing via state or separate route
      // For now, let's navigate to a hypothetical edit route or reuse new with state
      navigate('/patients/new', { state: { patient: currentPatient } });
    }
  };

  if (error) {
    return (
      <div
        style={{
          padding: spacing.lg,
          backgroundColor: `${colors.alert.critical}15`,
          border: `2px solid ${colors.alert.critical}`,
          borderRadius: "8px",
          color: colors.alert.critical,
          margin: spacing.lg
        }}
      >
        <strong>Erro:</strong> {error}
      </div>
    );
  }

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "400px",
          fontSize: "1.125rem",
          color: colors.text.secondary,
        }}
      >
        <span style={{ animation: "spin 1s linear infinite" }}>⟳</span>
        &nbsp; Carregando informações do paciente...
      </div>
    );
  }

  const mockPatient = currentPatient;

  if (!mockPatient || !isValidPatientResource(mockPatient)) {
    return (
      <div style={{ padding: spacing.lg, textAlign: "center", color: colors.text.secondary }}>
        Paciente não encontrado ou dados inválidos.
      </div>
    );
  }

  const summary = getPatientSummary(mockPatient);
  return (
    <div style={{ backgroundColor: "#f8fafc", minHeight: "100vh" }}>
      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: spacing.md }}>
        <Button
          variant="secondary"
          onClick={() => navigate('/')}
          style={{ marginBottom: spacing.md }}
        >
          &larr; Voltar para Lista de Pacientes
        </Button>

        <div style={{
          backgroundColor: colors.primary.medium,
          color: "white",
          borderRadius: "12px",
          padding: spacing.lg,
          marginTop: spacing.xl,
          marginBottom: spacing.xl,
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: spacing.md
        }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, lineHeight: 1.2 }}>
              {summary.name}
            </h1>
            <p style={{ margin: "4px 0 0 0", opacity: 0.9, fontSize: "0.9rem" }}>
              ID: <span style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.2)', padding: '2px 6px', borderRadius: '4px' }}>{mockPatient.id}</span> • {summary.gender} • {summary.age ? `${summary.age} anos` : 'Idade N/A'}
            </p>
          </div>

          <div style={{ display: "flex", gap: spacing.sm }}>
            <Button onClick={() => setView(view === 'clinical' ? 'overview' : 'clinical')} style={{ backgroundColor: 'white', color: colors.primary.dark }}>
              ▶ {view === 'clinical' ? 'Fechar Atendimento' : 'Iniciar Atendimento'}
            </Button>
            <Button variant="secondary" onClick={handleEdit} style={{ borderColor: 'rgba(255,255,255,0.3)', color: 'white', backgroundColor: 'transparent' }}>
              ✎ Editar
            </Button>
            <Button
              variant="secondary"
              style={{
                borderColor: '#ef4444',
                color: '#ef4444',
                backgroundColor: 'rgba(255,255,255,0.1)',
              }}
              onClick={handleDelete}
            >
              🗑 Excluir
            </Button>
          </div>
        </div >


        {/* Section: Resumo Estruturado */}
        <section style={{ marginBottom: spacing.xl }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: spacing.lg,
            }}
          >
            {/* Card: Dados Nascimento */}
            <Card padding="lg">
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: colors.text.tertiary, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Nascimento
              </label>
              <div style={{ fontSize: "1.125rem", fontWeight: 500, color: colors.text.primary, marginTop: '4px' }}>
                {summary.birthDateFormatted}
              </div>
            </Card>

            {/* Card: CPF/Documentos */}
            <Card padding="lg">
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: colors.text.tertiary, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                CPF
              </label>
              <div style={{ fontSize: "1.125rem", fontWeight: 500, color: colors.text.primary, marginTop: '4px', fontFamily: 'monospace' }}>
                {summary.cpf || "—"}
              </div>
            </Card>

            {/* Card: Contato Principal */}
            <Card padding="lg">
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: colors.text.tertiary, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Contato
              </label>
              <div style={{ fontSize: "1rem", fontWeight: 500, color: colors.primary.medium, marginTop: '4px' }}>
                {summary.telecom?.[0]?.value || "Sem contato"}
              </div>
            </Card>
          </div>
        </section>

        {view === 'overview' && (
          <>
            {/* Section: Sinais Vitais */}
            <section style={{ marginBottom: spacing.xl }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: spacing.md, color: colors.text.primary, borderLeft: `4px solid ${colors.primary.medium}`, paddingLeft: spacing.sm }}>
                Sinais Vitais 🩺
              </h2>
              <VitalSigns patientId={mockPatient.id} />
            </section>

            {/* Layout em Grid para Listas Clinicas */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: spacing.lg, marginBottom: spacing.xl }}>
              {/* Módulos e Histórico */}
              <section>
                <div className="mb-6">
                  <Card className="p-4 bg-slate-50 border border-slate-200">
                    <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                      <Activity size={18} className="text-indigo-600" />
                      Módulos Clínicos
                    </h3>
                    <div className="flex gap-2 flex-wrap">
                      <Button variant="outline" onClick={() => setView('immunization')}>
                        💉 Vacinas
                      </Button>
                      <Button variant="outline" onClick={() => setView('diagnostic')}>
                        📑 Resultados de Exames
                      </Button>
                    </div>
                  </Card>
                </div>

                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: spacing.md, color: colors.text.primary, borderLeft: `4px solid ${colors.accent.primary}`, paddingLeft: spacing.sm }}>
                  Histórico Clínico
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
                  <ProblemList patientId={mockPatient.id} />
                  <AllergyList patientId={mockPatient.id} />
                </div>
              </section>

              {/* Atendimentos e Agendamentos */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.xl }}>
                <section>
                  <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: spacing.md, color: colors.text.primary, borderLeft: `4px solid ${colors.primary.dark}`, paddingLeft: spacing.sm }}>
                    Timeline de Atendimentos
                  </h2>
                  <EncounterList
                    patientId={mockPatient.id}
                    onStartEncounter={() => setView('clinical')}
                  />
                </section>

                <section>
                  <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: spacing.md, color: colors.text.primary, borderLeft: `4px solid ${colors.primary.medium}`, paddingLeft: spacing.sm }}>
                    Agendamentos
                  </h2>
                  <AppointmentList patientId={mockPatient.id} />
                </section>
              </div>
            </div>
          </>
        )}

        {view === 'clinical' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <ClinicalWorkspace />
          </div>
        )}

        {view === 'immunization' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <ImmunizationWorkspace />
          </div>
        )}

        {view === 'diagnostic' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <DiagnosticResultWorkspace />
          </div>
        )}

        {/* Section: JSON FHIR (Debug/Advanced) */}
        <section>
          <details style={{ cursor: "pointer" }}>
            <summary style={{ fontSize: '0.8rem', color: colors.text.tertiary }}>
              🔧 Dados Brutos (FHIR Resource)
            </summary>
            <pre style={{ marginTop: spacing.sm, padding: spacing.md, backgroundColor: '#f8fafc', borderRadius: "8px", fontSize: "0.7rem", overflow: "auto", border: `1px solid ${colors.border.default}` }}>
              {JSON.stringify(mockPatient, null, 2)}
            </pre>
          </details>
        </section>
      </main>
    </div >
  );
};

export default PatientDetail;
