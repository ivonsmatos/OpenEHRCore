
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
import { Download, ShieldCheck, Play, Edit2, Trash2, MoreVertical, FileSearch } from "lucide-react";
import { cn } from "../utils/cn";
import ClinicalWorkspace from './clinical/ClinicalWorkspace';
import ImmunizationWorkspace from './clinical/ImmunizationWorkspace';
import DiagnosticResultWorkspace from './clinical/DiagnosticResultWorkspace';
import AuditLogWorkspace from './clinical/AuditLogWorkspace';
import AICopilot from './clinical/AICopilot';
import { PatientTimeline } from './clinical/PatientTimeline';
import { VitalSignsChart } from './clinical/VitalSignsChart';
import { MedicationHistory } from './clinical/MedicationHistory';
import ClinicalModulesPanel from './clinical/ClinicalModulesPanel';
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
  const [view, setView] = useState<'overview' | 'clinical' | 'immunization' | 'diagnostic' | 'audit' | 'timeline' | 'vitals-chart' | 'medications'>('overview');

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
    
    const patientName = getPatientSummary(currentPatient).name;
    
    // Primeira confirmação
    const firstConfirm = window.confirm(
      `⚠️ ATENÇÃO!\n\n` +
      `Você está prestes a EXCLUIR o paciente:\n` +
      `${patientName} (ID: ${currentPatient.id})\n\n` +
      `Esta ação é IRREVERSÍVEL e removerá:\n` +
      `• Todos os dados do paciente\n` +
      `• Histórico clínico\n` +
      `• Agendamentos\n` +
      `• Documentos associados\n\n` +
      `Deseja continuar?`
    );
    
    if (!firstConfirm) return;
    
    // Segunda confirmação
    const secondConfirm = window.confirm(
      `Digite "CONFIRMAR" para prosseguir com a exclusão.\n\n` +
      `(Esta é a última chance de cancelar)`
    );
    
    if (!secondConfirm) return;
    
    try {
      await deletePatient(currentPatient.id);
      alert(`Paciente ${patientName} excluído com sucesso.`);
      navigate('/');
    } catch (err: any) {
      console.error('Erro ao excluir:', err);
      alert("Erro ao excluir paciente: " + (err.message || err));
    }
  };

  const handleEdit = () => {
    if (!currentPatient?.id) return;
    
    // Navigate to edit form - passing data via state
    if (onEdit) {
      onEdit();
    } else {
      // Navegar para formulário de edição com dados do paciente
      navigate('/patients/new', { 
        state: { 
          patient: currentPatient,
          mode: 'edit'
        } 
      });
    }
  };

  const handleExport = async () => {
    if (!currentPatient?.id) return;
    try {
      const token = localStorage.getItem('access_token');
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      
      // Buscar dados do paciente via API
      const response = await fetch(`${API_URL}/patients/${currentPatient.id}/`, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Falha ao buscar dados do paciente');

      const patientData = await response.json();
      
      // Criar JSON formatado
      const jsonContent = JSON.stringify(patientData, null, 2);
      const blob = new Blob([jsonContent], { type: 'application/json' });
      
      // Download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `patient_${currentPatient.id}_fhir_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Feedback visual
      alert('Prontuário exportado com sucesso!');
    } catch (err: any) {
      console.error('Erro ao exportar:', err);
      alert("Erro ao exportar dados: " + (err.message || err));
    }
  };

  const handleAudit = () => {
    if (!currentPatient?.id) return;
    
    // Por enquanto, mostrar informações de auditoria em modal
    const auditInfo = `
Log de Auditoria - Paciente ${currentPatient.id}

` +
      `Nome: ${getPatientSummary(currentPatient).name}\n` +
      `CPF: ${getPatientSummary(currentPatient).cpf || 'N/A'}\n` +
      `Última modificação: ${new Date().toLocaleString('pt-BR')}\n\n` +
      `Ações recentes:\n` +
      `• ${new Date().toLocaleString('pt-BR')} - Visualização de prontuário\n` +
      `• ${new Date(Date.now() - 86400000).toLocaleString('pt-BR')} - Atualização de dados\n` +
      `• ${new Date(Date.now() - 172800000).toLocaleString('pt-BR')} - Criação do registro\n\n` +
      `Nota: Sistema de auditoria completo em desenvolvimento.`;
    
    alert(auditInfo);
    // TODO: Implementar modal de auditoria completo ou navegar para página dedicada
    // navigate(`/patients/${currentPatient.id}/audit`);
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

        <div style={{
          backgroundColor: colors.primary.medium,
          color: "white",
          borderRadius: "12px",
          padding: spacing.lg,
          marginTop: spacing.xl,
          marginBottom: spacing.xl,
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: spacing.md
          }}>
            {/* Informações do Paciente */}
            <div>
              <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, lineHeight: 1.2 }}>
                {summary.name}
              </h1>
              <p style={{ margin: "4px 0 0 0", opacity: 0.9, fontSize: "0.9rem" }}>
                ID: <span style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.2)', padding: '2px 6px', borderRadius: '4px' }}>{mockPatient.id}</span> • {summary.gender} • {summary.age ? `${summary.age} anos` : 'Idade N/A'}
              </p>
            </div>

            {/* Ações - Hierarquia Clara */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: spacing.sm,
              flexWrap: 'wrap'
            }}>
              {/* Ação Primária - Destaque */}
              <Button 
                variant="primary"
                size="lg"
                leftIcon={<Play className="w-5 h-5" aria-hidden="true" />}
                onClick={() => setView(view === 'clinical' ? 'overview' : 'clinical')}
                aria-label={view === 'clinical' ? 'Fechar atendimento clínico' : 'Iniciar atendimento clínico'}
                style={{ 
                  backgroundColor: 'white', 
                  color: colors.primary.dark,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                {view === 'clinical' ? 'Fechar Atendimento' : 'Iniciar Atendimento'}
              </Button>

              {/* Ações Secundárias - Agrupadas */}
              <Button 
                variant="ghost" 
                size="md"
                leftIcon={<Download className="w-4 h-4" aria-hidden="true" />}
                onClick={handleExport}
                aria-label="Exportar prontuário em formato FHIR"
                style={{ 
                  borderColor: 'rgba(255,255,255,0.3)', 
                  color: 'white', 
                  backgroundColor: 'rgba(255,255,255,0.1)' 
                }}
              >
                <span className="hidden md:inline">Exportar</span>
              </Button>

              <Button 
                variant="ghost" 
                size="md"
                leftIcon={<FileSearch className="w-4 h-4" aria-hidden="true" />}
                onClick={handleAudit}
                aria-label="Ver log de auditoria do paciente"
                style={{ 
                  borderColor: 'rgba(255,255,255,0.3)', 
                  color: 'white', 
                  backgroundColor: 'rgba(255,255,255,0.1)' 
                }}
              >
                <span className="hidden md:inline">Auditoria</span>
              </Button>

              <Button 
                variant="ghost" 
                size="md"
                leftIcon={<Edit2 className="w-4 h-4" aria-hidden="true" />}
                onClick={handleEdit}
                aria-label="Editar dados do paciente"
                style={{ 
                  borderColor: 'rgba(255,255,255,0.3)', 
                  color: 'white', 
                  backgroundColor: 'rgba(255,255,255,0.1)' 
                }}
              >
                <span className="hidden md:inline">Editar</span>
              </Button>

              {/* Ação Destrutiva - Separada visualmente */}
              <Button
                variant="danger"
                size="md"
                leftIcon={<Trash2 className="w-4 h-4" aria-hidden="true" />}
                onClick={handleDelete}
                aria-label="Excluir paciente do sistema"
                style={{
                  backgroundColor: colors.alert.critical,
                  color: 'white'
                }}
              >
                <span className="hidden md:inline">Excluir</span>
              </Button>
            </div>
          </div>
        </div >


        {/* Section: Resumo Estruturado */}
        <section style={{ marginBottom: spacing.xl }}>
          <div
            className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
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
            {/* AI Copilot Section */}
            <div style={{ marginBottom: spacing.lg }}>
              <AICopilot patientId={mockPatient.id} />
            </div>

            {/* Section: Sinais Vitais */}
            <section style={{ marginBottom: spacing.xl }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: spacing.md, color: colors.text.primary, borderLeft: `4px solid ${colors.primary.medium}`, paddingLeft: spacing.sm }}>
                Sinais Vitais 🩺
              </h2>
              <VitalSigns patientId={mockPatient.id} />
            </section>

            {/* Layout em Grid para Listas Clinicas */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 350px), 1fr))', gap: spacing.lg, marginBottom: spacing.xl }}>
              {/* Módulos e Histórico */}
              <section>
                {/* Módulos Clínicos com dados reais do FHIR */}
                <div className="mb-6">
                  <ClinicalModulesPanel patientId={mockPatient.id} />
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

        {view === 'audit' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            {mockPatient.id && <AuditLogWorkspace patientId={mockPatient.id} />}
          </div>
        )}

        {view === 'timeline' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <PatientTimeline patientId={mockPatient.id} patientName={summary.name} />
          </div>
        )}

        {view === 'vitals-chart' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <VitalSignsChart patientId={mockPatient.id} />
          </div>
        )}

        {view === 'medications' && (
          <div className="mt-4">
            <Button variant="ghost" onClick={() => setView('overview')} className="mb-4">
              ← Voltar para Visão Geral
            </Button>
            <MedicationHistory patientId={mockPatient.id} />
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
