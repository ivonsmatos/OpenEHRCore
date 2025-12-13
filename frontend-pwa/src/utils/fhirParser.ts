/**
 * Utilitários para parsing seguro de recursos FHIR
 *
 * Estas funções extraem dados do JSON complexo do FHIR
 * de forma robusta, tratando arrays vazios e estruturas ausentes.
 */

export interface FHIRPatient {
  resourceType: string;
  id: string;
  name?: Array<{
    family?: string;
    given?: string[];
    use?: string;
  }>;
  birthDate?: string;
  gender?: string;
  telecom?: Array<{
    system: string;
    value: string;
  }>;
  identifier?: Array<{
    system: string;
    value: string;
    type?: {
      coding?: Array<{
        code: string;
        display?: string;
      }>;
    };
  }>;
  address?: Array<{
    line?: string[];
    city?: string;
    state?: string;
    postalCode?: string;
  }>;
  [key: string]: any;
}

/**
 * Extrai nome completo de forma segura
 * Trata: arrays vazios, nomes sem family/given, múltiplos nomes
 */
export function getPatientFullName(patient: FHIRPatient): string {
  if (!patient.name || patient.name.length === 0) {
    return "Sem nome registrado";
  }

  const officialName =
    patient.name.find((n) => n.use === "official") || patient.name[0];

  if (!officialName) {
    return "Sem nome registrado";
  }

  const family = officialName.family || "";
  const given = (officialName.given || []).join(" ");

  return `${given} ${family}`.trim() || "Sem nome registrado";
}

/**
 * Extrai primeiro nome
 */
export function getPatientFirstName(patient: FHIRPatient): string {
  if (!patient.name || patient.name.length === 0) {
    return "";
  }

  const firstName = patient.name[0].given?.[0] || "";
  return firstName;
}

/**
 * Extrai sobrenome
 */
export function getPatientLastName(patient: FHIRPatient): string {
  if (!patient.name || patient.name.length === 0) {
    return "";
  }

  return patient.name[0].family || "";
}

/**
 * Extrai CPF (identifier do sistema CPF)
 */
export function getPatientCPF(patient: FHIRPatient): string | null {
  if (!patient.identifier || patient.identifier.length === 0) return null;

  const cpfIdentifier = patient.identifier.find((id) => {
    const system = (id.system || '').toLowerCase();
    const codings = id.type?.coding || [];

    const systemMatches = system === 'http://openehrcore.com.br/cpf' || system === 'http://gov.br/cpf' || system === 'http://gov.br/cpf/';

    const codeMatches = codings.some(c => {
      const code = (c.code || '').toString().toUpperCase();
      return code === 'CPF' || code === 'TAX';
    });

    return systemMatches || codeMatches;
  });

  return cpfIdentifier?.value || null;
}

/**
 * Formata data FHIR (YYYY-MM-DD) para formato local
 * Suporta múltiplos locales
 */
export function formatPatientBirthDate(
  birthDate: string | undefined,
  locale: string = "pt-BR"
): string {
  if (!birthDate) {
    return "Data não registrada";
  }

  try {
    const date = new Date(`${birthDate}T00:00:00Z`);

    if (isNaN(date.getTime())) {
      return "Data inválida";
    }

    return new Intl.DateTimeFormat(locale, {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }).format(date);
  } catch {
    return "Data inválida";
  }
}

/**
 * Calcula idade a partir de birthDate
 */
export function calculatePatientAge(birthDate: string | undefined): number | null {
  if (!birthDate) {
    return null;
  }

  try {
    const birth = new Date(`${birthDate}T00:00:00Z`);
    const today = new Date();

    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();

    if (
      monthDiff < 0 ||
      (monthDiff === 0 && today.getDate() < birth.getDate())
    ) {
      age--;
    }

    return age >= 0 ? age : null;
  } catch {
    return null;
  }
}

/**
 * Extrai contatos (telecom) de forma segura
 */
export function getPatientTelecom(
  patient: FHIRPatient
): Array<{ system: string; value: string; display: string }> {
  if (!patient.telecom || patient.telecom.length === 0) {
    return [];
  }

  return patient.telecom.map((t) => ({
    system: t.system,
    value: t.value,
    display:
      t.system === "phone"
        ? `📞 ${t.value}`
        : t.system === "email"
          ? `📧 ${t.value}`
          : t.value,
  }));
}

/**
 * Extrai gênero com label amigável
 */
export function getPatientGenderLabel(gender: string | undefined): string {
  const genderMap: Record<string, string> = {
    male: "Masculino",
    female: "Feminino",
    other: "Outro",
    unknown: "Não especificado",
  };

  return genderMap[gender || "unknown"] || "Não especificado";
}

/**
 * Extrai endereço formatado
 */
export function getPatientAddress(patient: FHIRPatient): string {
  if (!patient.address || patient.address.length === 0) {
    return "Sem endereço registrado";
  }

  const addr = patient.address[0];
  const parts = [];

  if (addr.line && addr.line.length > 0) {
    parts.push(addr.line.join(", "));
  }

  if (addr.city) {
    parts.push(addr.city);
  }

  if (addr.state) {
    parts.push(addr.state);
  }

  if (addr.postalCode) {
    parts.push(addr.postalCode);
  }

  return parts.length > 0 ? parts.join(" - ") : "Sem endereço registrado";
}

/**
 * Validação básica do recurso Patient
 */
export function isValidPatientResource(patient: any): patient is FHIRPatient {
  return (
    patient &&
    typeof patient === "object" &&
    patient.resourceType === "Patient" &&
    typeof patient.id === "string" &&
    patient.id.length > 0
  );
}

/**
 * Resume do paciente para exibição rápida
 */
export function getPatientSummary(patient: FHIRPatient) {
  const firstName = getPatientFirstName(patient);
  const lastName = getPatientLastName(patient);
  const initials = `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();

  return {
    id: patient.id,
    name: getPatientFullName(patient),
    firstName,
    lastName,
    initials,
    cpf: getPatientCPF(patient),
    birthDate: patient.birthDate,
    birthDateFormatted: formatPatientBirthDate(patient.birthDate),
    age: calculatePatientAge(patient.birthDate),
    gender: getPatientGenderLabel(patient.gender),
    telecom: getPatientTelecom(patient),
    address: getPatientAddress(patient),
  };
}

// ----------------------------------------------------------------------
// OBSERVATION (Sinais Vitais)
// ----------------------------------------------------------------------

export interface FHIRObservation {
  resourceType: string;
  id: string;
  status: string;
  code: {
    coding: Array<{
      system: string;
      code: string;
      display?: string;
    }>;
    text?: string;
  };
  subject: {
    reference: string;
  };
  valueQuantity?: {
    value: number;
    unit?: string;
    system?: string;
    code?: string;
  };
  component?: Array<{
    code: {
      coding: Array<{
        system: string;
        code: string;
        display?: string;
      }>;
      text?: string;
    };
    valueQuantity: {
      value: number;
      unit?: string;
      system?: string;
      code?: string;
    };
  }>;
  effectiveDateTime?: string;
  [key: string]: any;
}

/**
 * Extrai o nome da observação (ex: "Blood Pressure")
 */
export function getObservationName(obs: FHIRObservation): string {
  if (obs.code?.text) return obs.code.text;
  if (obs.code?.coding?.[0]?.display) return obs.code.coding[0].display;
  return "Observação sem nome";
}

/**
 * Extrai o valor formatado (ex: "120 mmHg" ou "120/80 mmHg")
 */
export function getObservationValue(obs: FHIRObservation): string {
  // 1. Caso ValueQuantity simples (Peso, Altura, Temp)
  if (obs.valueQuantity) {
    let val = obs.valueQuantity.value;
    const unit = obs.valueQuantity.unit || "";

    // Rounding logic: Max 2 decimals, remove trailing zeros
    if (typeof val === 'number') {
      const rounded = +val.toFixed(2); // Unary plus converts back to number
      return `${rounded} ${unit}`.trim();
    }
    return `${val} ${unit}`.trim();
  }

  // 2. Caso Componentes (Pressão Arterial)
  // Blood Pressure usually stores Systolic (8480-6) and Diastolic (8462-4) in components
  if (obs.component && obs.component.length > 0) {
    const systolic = obs.component.find(c => c.code?.coding?.some(acc => acc.code === '8480-6'));
    const diastolic = obs.component.find(c => c.code?.coding?.some(acc => acc.code === '8462-4'));

    if (systolic?.valueQuantity && diastolic?.valueQuantity) {
      const sysVal = Math.round(systolic.valueQuantity.value);
      const diaVal = Math.round(diastolic.valueQuantity.value);
      const unit = systolic.valueQuantity.unit || "mmHg";
      return `${sysVal}/${diaVal} ${unit}`;
    }

    // Generic fallback for other components: show first component value
    const first = obs.component[0];
    if (first.valueQuantity) {
      const val = +first.valueQuantity.value.toFixed(2);
      const unit = first.valueQuantity.unit || "";
      return `${val} ${unit}`;
    }
  }

  return "Sem valor";
}

/**
 * Formata data da observação
 */
export function formatObservationDate(dateString?: string): string {
  if (!dateString) return "-";
  try {
    return new Date(dateString).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

// ----------------------------------------------------------------------
// CONDITION (Problemas/Diagnósticos)
// ----------------------------------------------------------------------

export interface FHIRCondition {
  resourceType: string;
  id: string;
  clinicalStatus?: {
    coding: Array<{ code: string }>;
  };
  verificationStatus?: {
    coding: Array<{ code: string }>;
  };
  code?: {
    text?: string;
    coding?: Array<{ display?: string; code: string }>;
  };
  recordedDate?: string;
  [key: string]: any;
}

export function getConditionName(cond: FHIRCondition): string {
  return cond.code?.text || cond.code?.coding?.[0]?.display || "Condição sem nome";
}

export function getConditionStatus(cond: FHIRCondition): string {
  return cond.clinicalStatus?.coding?.[0]?.code || "unknown";
}

// ----------------------------------------------------------------------
// ALLERGY INTOLERANCE (Alergias)
// ----------------------------------------------------------------------

export interface FHIRAllergyIntolerance {
  resourceType: string;
  id: string;
  clinicalStatus?: {
    coding: Array<{ code: string }>;
  };
  criticality?: "low" | "high" | "unable-to-assess";
  code?: {
    text?: string;
    coding?: Array<{ display?: string; code: string }>;
  };
  recordedDate?: string;
  [key: string]: any;
}

export function getAllergyName(allergy: FHIRAllergyIntolerance): string {
  return allergy.code?.text || allergy.code?.coding?.[0]?.display || "Alergia sem nome";
}

export function getAllergyCriticality(allergy: FHIRAllergyIntolerance): string {
  const map: Record<string, string> = {
    low: "Baixa",
    high: "Alta",
    "unable-to-assess": "Desconhecida",
  };
  return map[allergy.criticality || ""] || "Desconhecida";
}

// ----------------------------------------------------------------------
// APPOINTMENT (Agendamento)
// ----------------------------------------------------------------------

export interface FHIRAppointment {
  resourceType: string;
  id: string;
  status: string;
  description?: string;
  start?: string;
  end?: string;
  participant?: Array<{
    actor?: { reference: string; display?: string };
    status: string;
  }>;
  [key: string]: any;
}

export function getAppointmentDescription(appt: FHIRAppointment): string {
  return appt.description || "Consulta sem descrição";
}

export function formatAppointmentDate(dateString?: string): string {
  if (!dateString) return "Data não definida";
  try {
    return new Date(dateString).toLocaleString("pt-BR", {
      weekday: "short",
      day: "2-digit",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

export function getAppointmentStatusLabel(status: string): string {
  const map: Record<string, string> = {
    proposed: "Proposto",
    pending: "Pendente",
    booked: "Agendado",
    arrived: "Chegou",
    fulfilled: "Realizado",
    cancelled: "Cancelado",
    noshow: "Não compareceu",
    "entered-in-error": "Erro",
    "checked-in": "Check-in",
    waitlist: "Lista de espera",
  };
  return map[status] || status;
}
