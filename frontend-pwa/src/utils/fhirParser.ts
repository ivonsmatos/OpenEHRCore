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
  if (!patient.identifier || patient.identifier.length === 0) {
    return null;
  }

  const cpfIdentifier = patient.identifier.find(
    (id) =>
      id.system === "http://openehrcore.com.br/cpf" ||
      id.type?.coding?.[0]?.code === "CPF"
  );

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
  return {
    id: patient.id,
    name: getPatientFullName(patient),
    firstName: getPatientFirstName(patient),
    lastName: getPatientLastName(patient),
    cpf: getPatientCPF(patient),
    birthDate: patient.birthDate,
    birthDateFormatted: formatPatientBirthDate(patient.birthDate),
    age: calculatePatientAge(patient.birthDate),
    gender: getPatientGenderLabel(patient.gender),
    telecom: getPatientTelecom(patient),
    address: getPatientAddress(patient),
  };
}
