"""
FHIR StructureDefinition - Practitioner BR (RNDS)

Perfil brasileiro para Practitioner baseado em:
- https://rnds-fhir.saude.gov.br/
- https://simplifier.net/redenacionaldedadosemsaude

Sprint 36: Conformidade RNDS
"""

PRACTITIONER_BR_PROFILE = {
    "resourceType": "StructureDefinition",
    "id": "BRProfissional-1.0",
    "url": "http://openehrcore.com.br/fhir/StructureDefinition/BRProfissional",
    "version": "1.0.0",
    "name": "BRProfissional",
    "title": "Profissional de Saúde (Practitioner BR)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Perfil brasileiro para Practitioner, compatível com RNDS",
    "fhirVersion": "4.0.1",
    "kind": "resource",
    "abstract": False,
    "type": "Practitioner",
    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Practitioner",
    "derivation": "constraint",
    "differential": {
        "element": [
            {
                "id": "Practitioner",
                "path": "Practitioner",
                "short": "Profissional de saúde no contexto brasileiro",
                "definition": "Profissional com identificadores brasileiros (CPF, CRM, COREN, etc)"
            },
            # Identifier - slicing
            {
                "id": "Practitioner.identifier",
                "path": "Practitioner.identifier",
                "slicing": {
                    "discriminator": [
                        {
                            "type": "value",
                            "path": "system"
                        }
                    ],
                    "rules": "open"
                },
                "min": 1,
                "max": "*"
            },
            # CPF
            {
                "id": "Practitioner.identifier:cpf",
                "path": "Practitioner.identifier",
                "sliceName": "cpf",
                "short": "CPF do profissional",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:cpf.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf"
            },
            {
                "id": "Practitioner.identifier:cpf.value",
                "path": "Practitioner.identifier.value",
                "min": 1,
                "constraint": [
                    {
                        "key": "cpf-valid",
                        "severity": "error",
                        "human": "CPF deve ter 11 dígitos numéricos",
                        "expression": "matches('^[0-9]{11}$')"
                    }
                ]
            },
            # CNS
            {
                "id": "Practitioner.identifier:cns",
                "path": "Practitioner.identifier",
                "sliceName": "cns",
                "short": "CNS do profissional",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:cns.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns"
            },
            # CRM (Médico)
            {
                "id": "Practitioner.identifier:crm",
                "path": "Practitioner.identifier",
                "sliceName": "crm",
                "short": "CRM do médico",
                "definition": "Conselho Regional de Medicina",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:crm.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm"
            },
            {
                "id": "Practitioner.identifier:crm.value",
                "path": "Practitioner.identifier.value",
                "short": "Número CRM/UF (ex: 123456/SP)",
                "min": 1
            },
            # COREN (Enfermeiro)
            {
                "id": "Practitioner.identifier:coren",
                "path": "Practitioner.identifier",
                "sliceName": "coren",
                "short": "COREN do enfermeiro",
                "definition": "Conselho Regional de Enfermagem",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:coren.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/coren"
            },
            # CRO (Dentista)
            {
                "id": "Practitioner.identifier:cro",
                "path": "Practitioner.identifier",
                "sliceName": "cro",
                "short": "CRO do dentista",
                "definition": "Conselho Regional de Odontologia",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:cro.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cro"
            },
            # CRF (Farmacêutico)
            {
                "id": "Practitioner.identifier:crf",
                "path": "Practitioner.identifier",
                "sliceName": "crf",
                "short": "CRF do farmacêutico",
                "definition": "Conselho Regional de Farmácia",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:crf.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crf"
            },
            # CRP (Psicólogo)
            {
                "id": "Practitioner.identifier:crp",
                "path": "Practitioner.identifier",
                "sliceName": "crp",
                "short": "CRP do psicólogo",
                "definition": "Conselho Regional de Psicologia",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Practitioner.identifier:crp.system",
                "path": "Practitioner.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crp"
            },
            # Nome
            {
                "id": "Practitioner.name",
                "path": "Practitioner.name",
                "min": 1,
                "max": "*"
            },
            {
                "id": "Practitioner.name.text",
                "path": "Practitioner.name.text",
                "short": "Nome completo do profissional",
                "min": 1
            },
            # Qualification (especialidade)
            {
                "id": "Practitioner.qualification",
                "path": "Practitioner.qualification",
                "short": "Qualificações e especialidades",
                "min": 0,
                "max": "*"
            },
            {
                "id": "Practitioner.qualification.code",
                "path": "Practitioner.qualification.code",
                "binding": {
                    "strength": "extensible",
                    "valueSet": "http://openehrcore.com.br/fhir/ValueSet/BREspecialidadeMedica"
                }
            },
            {
                "id": "Practitioner.qualification.issuer",
                "path": "Practitioner.qualification.issuer",
                "short": "Conselho emissor (CRM, COREN, etc)",
                "type": [
                    {
                        "code": "Reference",
                        "targetProfile": [
                            "http://hl7.org/fhir/StructureDefinition/Organization"
                        ]
                    }
                ]
            }
        ]
    }
}


# ValueSet para especialidades médicas (CBO)
ESPECIALIDADE_MEDICA_VALUESET = {
    "resourceType": "ValueSet",
    "id": "BREspecialidadeMedica",
    "url": "http://openehrcore.com.br/fhir/ValueSet/BREspecialidadeMedica",
    "version": "1.0.0",
    "name": "BREspecialidadeMedica",
    "title": "Especialidades Médicas - Brasil (CBO)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Códigos de especialidades médicas conforme CBO",
    "compose": {
        "include": [
            {
                "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRCBO",
                "concept": [
                    {"code": "2251-01", "display": "Médico acupunturista"},
                    {"code": "2251-02", "display": "Médico alergista e imunologista"},
                    {"code": "2251-03", "display": "Médico anatomopatologista"},
                    {"code": "2251-04", "display": "Médico anestesiologista"},
                    {"code": "2251-05", "display": "Médico angiologista"},
                    {"code": "2251-06", "display": "Médico cardiologista"},
                    {"code": "2251-07", "display": "Médico cirurgião cardiovascular"},
                    {"code": "2251-08", "display": "Médico cirurgião de cabeça e pescoço"},
                    {"code": "2251-09", "display": "Médico cirurgião do aparelho digestivo"},
                    {"code": "2251-10", "display": "Médico cirurgião geral"},
                    {"code": "2251-11", "display": "Médico cirurgião pediátrico"},
                    {"code": "2251-12", "display": "Médico cirurgião plástico"},
                    {"code": "2251-13", "display": "Médico cirurgião torácico"},
                    {"code": "2251-14", "display": "Médico citopatologista"},
                    {"code": "2251-15", "display": "Médico clínico"},
                    {"code": "2251-16", "display": "Médico coloproctologista"},
                    {"code": "2251-17", "display": "Médico dermatologista"},
                    {"code": "2251-18", "display": "Médico do trabalho"},
                    {"code": "2251-19", "display": "Médico em cirurgia vascular"},
                    {"code": "2251-20", "display": "Médico em medicina de tráfego"},
                    {"code": "2251-21", "display": "Médico em medicina intensiva"},
                    {"code": "2251-22", "display": "Médico em medicina nuclear"},
                    {"code": "2251-23", "display": "Médico em medicina preventiva e social"},
                    {"code": "2251-24", "display": "Médico endocrinologista e metabologista"},
                    {"code": "2251-25", "display": "Médico fisiatra"},
                    {"code": "2251-26", "display": "Médico gastroenterologista"},
                    {"code": "2251-27", "display": "Médico geneticista"},
                    {"code": "2251-28", "display": "Médico geriatra"},
                    {"code": "2251-29", "display": "Médico ginecologista e obstetra"},
                    {"code": "2251-30", "display": "Médico hematologista"},
                    {"code": "2251-31", "display": "Médico homeopata"},
                    {"code": "2251-32", "display": "Médico infectologista"},
                    {"code": "2251-33", "display": "Médico legista"},
                    {"code": "2251-34", "display": "Médico mastologista"},
                    {"code": "2251-35", "display": "Médico nefrologista"},
                    {"code": "2251-36", "display": "Médico neurocirurgião"},
                    {"code": "2251-37", "display": "Médico neurologista"},
                    {"code": "2251-38", "display": "Médico nutrologista"},
                    {"code": "2251-39", "display": "Médico oftalmologista"},
                    {"code": "2251-40", "display": "Médico oncologista clínico"},
                    {"code": "2251-41", "display": "Médico ortopedista e traumatologista"},
                    {"code": "2251-42", "display": "Médico otorrinolaringologista"},
                    {"code": "2251-43", "display": "Médico patologista clínico"},
                    {"code": "2251-44", "display": "Médico pediatra"},
                    {"code": "2251-45", "display": "Médico pneumologista"},
                    {"code": "2251-46", "display": "Médico psiquiatra"},
                    {"code": "2251-47", "display": "Médico radioterapeuta"},
                    {"code": "2251-48", "display": "Médico radiologista"},
                    {"code": "2251-49", "display": "Médico reumatologista"},
                    {"code": "2251-50", "display": "Médico urologista"},
                    {"code": "2252-05", "display": "Médico de família e comunidade"},
                    {"code": "2252-10", "display": "Médico de emergência"},
                    {"code": "2235-05", "display": "Enfermeiro"},
                    {"code": "2236-05", "display": "Fisioterapeuta"},
                    {"code": "2234-05", "display": "Farmacêutico"},
                    {"code": "2232-05", "display": "Cirurgião-dentista - clínico geral"},
                    {"code": "2515-10", "display": "Psicólogo clínico"},
                    {"code": "2237-10", "display": "Nutricionista"}
                ]
            }
        ]
    }
}
