import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePatients } from "../hooks/usePatients";
import Card from "./base/Card";
import Button from "./base/Button";
import Header from "./base/Header";
import VitalSigns from "./clinical/VitalSigns";
import ProblemList from "./clinical/ProblemList";
import AllergyList from "./clinical/AllergyList";
import EncounterList from "./clinical/EncounterList";
import AppointmentList from "./scheduling/AppointmentList";
import { colors, spacing } from "../theme/colors";
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
  const { patient, loading: propLoading, error: propError, onEdit, onDelete } = props;

  // Hook para buscar dados se não forem passados via props
  const { getPatient, loading: hookLoading, error: hookError } = usePatients();

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

  // Usar currentPatient para renderização
  const mockPatient = currentPatient; // Mantendo nome da variável para minimizar diff, mas idealmente renomearíamos

  if (error) {
    return (
      <div
        style={{
          padding: spacing.lg,
          backgroundColor: `${colors.alert.critical}15`,
          border: `2px solid ${colors.alert.critical}`,
          borderRadius: "8px",
          color: colors.alert.critical,
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

  if (!mockPatient || !isValidPatientResource(mockPatient)) {
    return (
      <div
        style={{
          padding: spacing.lg,
          textAlign: "center",
          color: colors.text.secondary,
        }}
      >
        Paciente não encontrado ou dados inválidos.
      </div>
    );
  }

  const summary = getPatientSummary(mockPatient);

  return (
    <div
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: spacing.lg,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <Header
        title="Detalhes do Paciente"
        subtitle="Visão unificada do prontuário eletrônico (FHIR)"
      >
        <div style={{ display: "flex", gap: spacing.sm }}>
          <Button onClick={() => navigate(`/patients/${mockPatient.id}/encounter/new`)}>
            ▶ Iniciar Atendimento
          </Button>
          <Button variant="secondary" onClick={onEdit}>
            Editar
          </Button>
          <Button
            variant="secondary"
            style={{
              border: `1px solid ${colors.alert.critical}`,
              color: colors.alert.critical,
              backgroundColor: "transparent",
            }}
            onClick={onDelete}
          >
            Excluir
          </Button>
        </div>
      </Header>

      <main>
        {/* Section: Resumo do Paciente */}
        <section style={{ marginBottom: spacing.xl }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: spacing.lg,
            }}
          >
            {/* Card: Identificação Principal */}
            <Card padding="lg">
              <div style={{ display: "flex", alignItems: "center", gap: spacing.md }}>
                <div
                  style={{
                    width: "64px",
                    height: "64px",
                    borderRadius: "50%",
                    backgroundColor: colors.primary.light,
                    color: colors.primary.dark,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.5rem",
                    fontWeight: 700,
                  }}
                >
                  {summary.initials}
                </div>
                <div
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: 600,
                    color: colors.primary.dark,
                  }}
                >
                  {summary.name}
                </div>
              </div>

              <div style={{ marginTop: spacing.md }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: colors.text.tertiary,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: "4px",
                  }}
                >
                  ID do Paciente
                </label>
                <code
                  style={{
                    fontSize: "0.875rem",
                    color: colors.text.secondary,
                    backgroundColor: colors.background.muted,
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontFamily: "monospace",
                  }}
                >
                  {mockPatient.id}
                </code>
              </div>
            </Card>

            {/* Card: Data de Nascimento e Idade */}
            <Card padding="lg">
              <div style={{ marginBottom: spacing.md }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: colors.text.tertiary,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: "4px",
                  }}
                >
                  Data de Nascimento
                </label>
                <div
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 500,
                    color: colors.text.primary,
                  }}
                >
                  {summary.birthDateFormatted}
                </div>
              </div>

              <div style={{ marginTop: spacing.md }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: colors.text.tertiary,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: "4px",
                  }}
                >
                  Idade
                </label>
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: colors.accent.primary,
                  }}
                >
                  {summary.age !== null ? `${summary.age} anos` : "N/A"}
                </div>
              </div>
            </Card>

            {/* Card: Gênero e CPF */}
            <Card padding="lg">
              <div style={{ marginBottom: spacing.md }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: colors.text.tertiary,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: "4px",
                  }}
                >
                  Gênero
                </label>
                <div
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 500,
                    color: colors.text.primary,
                  }}
                >
                  {summary.gender}
                </div>
              </div>

              <div style={{ marginTop: spacing.md }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: colors.text.tertiary,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: "4px",
                  }}
                >
                  CPF
                </label>
                <div
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 500,
                    color: colors.text.secondary,
                    fontFamily: "monospace",
                  }}
                >
                  {summary.cpf || "Não registrado"}
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Section: Sinais Vitais */}
        <section style={{ marginBottom: spacing.xl }}>
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginBottom: spacing.md,
              color: colors.text.primary,
              display: "flex",
              alignItems: "center",
              gap: spacing.sm,
            }}
          >
            Sinais Vitais 🩺
          </h2>
          <VitalSigns patientId={mockPatient.id} />
        </section>

        {/* Section: Histórico Clínico */}
        <section style={{ marginBottom: spacing.xl }}>
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginBottom: spacing.md,
              color: colors.text.primary,
            }}
          >
            Histórico Clínico
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: spacing.lg,
            }}
          >
            <div>
              <h3
                style={{
                  fontSize: "1.125rem",
                  fontWeight: 600,
                  marginBottom: spacing.sm,
                  color: colors.text.secondary,
                }}
              >
                Problemas / Condições
              </h3>
              <ProblemList patientId={mockPatient.id} />
            </div>
            <div>
              <h3
                style={{
                  fontSize: "1.125rem",
                  fontWeight: 600,
                  marginBottom: spacing.sm,
                  color: colors.text.secondary,
                }}
              >
                Alergias
              </h3>
              <AllergyList patientId={mockPatient.id} />
            </div>
          </div>
        </section>

        {/* Section: Atendimentos (Encounters) */}
        <section style={{ marginBottom: spacing.xl }}>
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginBottom: spacing.md,
              color: colors.text.primary,
            }}
          >
            Atendimentos 🩺
          </h2>
          <EncounterList
            patientId={mockPatient.id}
            onStartEncounter={() => navigate(`/patients/${mockPatient.id}/encounter/new`)}
          />
        </section>

        {/* Section: Agendamentos */}
        <section style={{ marginBottom: spacing.xl }}>
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              marginBottom: spacing.md,
              color: colors.text.primary,
            }}
          >
            Próximos Agendamentos 📅
          </h2>
          <AppointmentList patientId={mockPatient.id} />
        </section>

        {/* Section: Contatos */}
        {summary.telecom && summary.telecom.length > 0 && (
          <section style={{ marginBottom: spacing.xl }}>
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                marginBottom: spacing.md,
                color: colors.text.primary,
              }}
            >
              Contatos
            </h2>

            <Card padding="lg">
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                }}
              >
                {summary.telecom.map((contact, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: spacing.md,
                      paddingBottom: idx !== summary.telecom.length - 1 ? spacing.md : 0,
                      marginBottom: idx !== summary.telecom.length - 1 ? spacing.md : 0,
                      borderBottom:
                        idx !== summary.telecom.length - 1
                          ? `1px solid ${colors.border.light}`
                          : "none",
                    }}
                  >
                    <span style={{ fontSize: "1.25rem" }}>
                      {contact.system === "phone" ? "📞" : "📧"}
                    </span>
                    <div>
                      <div
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          color: colors.text.tertiary,
                          textTransform: "uppercase",
                        }}
                      >
                        {contact.system === "phone" ? "Telefone" : "E-mail"}
                      </div>
                      <a
                        href={
                          contact.system === "phone"
                            ? `tel:${contact.value}`
                            : `mailto:${contact.value}`
                        }
                        style={{
                          color: colors.primary.medium,
                          textDecoration: "none",
                          fontSize: "1rem",
                          fontWeight: 500,
                        }}
                      >
                        {contact.value}
                      </a>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          </section>
        )}

        {/* Section: Endereço */}
        {summary.address && summary.address !== "Sem endereço registrado" && (
          <section style={{ marginBottom: spacing.xl }}>
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                marginBottom: spacing.md,
                color: colors.text.primary,
              }}
            >
              Endereço
            </h2>

            <Card padding="lg">
              <p
                style={{
                  margin: 0,
                  fontSize: "1rem",
                  lineHeight: "1.5rem",
                  color: colors.text.secondary,
                }}
              >
                {summary.address}
              </p>
            </Card>
          </section>
        )}

        {/* Section: JSON FHIR (Debug) */}
        <section>
          <details
            style={{
              cursor: "pointer",
            }}
          >
            <summary
              style={{
                padding: spacing.md,
                backgroundColor: colors.background.muted,
                borderRadius: "8px",
                fontWeight: 600,
                color: colors.text.secondary,
                userSelect: "none",
              }}
            >
              🔍 Recurso FHIR (JSON)
            </summary>
            <pre
              style={{
                marginTop: spacing.md,
                padding: spacing.md,
                backgroundColor: colors.background.muted,
                borderRadius: "8px",
                fontSize: "0.75rem",
                overflow: "auto",
                color: colors.text.primary,
                border: `1px solid ${colors.border.light}`,
              }}
            >
              {JSON.stringify(mockPatient, null, 2)}
            </pre>
          </details>
        </section>
      </main>
    </div>
  );
};

export default PatientDetail;
