"""
FHIR StructureDefinition - Patient BR (RNDS)

Perfil brasileiro para Patient baseado em:
- https://rnds-fhir.saude.gov.br/
- https://simplifier.net/redenacionaldedadosemsaude

Sprint 36: Conformidade RNDS
"""

PATIENT_BR_PROFILE = {
    "resourceType": "StructureDefinition",
    "id": "BRIndividuo-1.0",
    "url": "http://openehrcore.com.br/fhir/StructureDefinition/BRIndividuo",
    "version": "1.0.0",
    "name": "BRIndividuo",
    "title": "Indivíduo (Patient BR)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Perfil brasileiro para Patient, compatível com RNDS",
    "fhirVersion": "4.0.1",
    "kind": "resource",
    "abstract": False,
    "type": "Patient",
    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
    "derivation": "constraint",
    "differential": {
        "element": [
            {
                "id": "Patient",
                "path": "Patient",
                "short": "Indivíduo no contexto brasileiro",
                "definition": "Paciente/indivíduo com identificadores brasileiros (CPF, CNS)"
            },
            # Identifier - CPF (obrigatório)
            {
                "id": "Patient.identifier",
                "path": "Patient.identifier",
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
            {
                "id": "Patient.identifier:cpf",
                "path": "Patient.identifier",
                "sliceName": "cpf",
                "short": "CPF do indivíduo",
                "definition": "Cadastro de Pessoa Física",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Patient.identifier:cpf.system",
                "path": "Patient.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf"
            },
            {
                "id": "Patient.identifier:cpf.value",
                "path": "Patient.identifier.value",
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
            {
                "id": "Patient.identifier:cns",
                "path": "Patient.identifier",
                "sliceName": "cns",
                "short": "CNS do indivíduo",
                "definition": "Cartão Nacional de Saúde",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Patient.identifier:cns.system",
                "path": "Patient.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns"
            },
            {
                "id": "Patient.identifier:cns.value",
                "path": "Patient.identifier.value",
                "min": 1,
                "constraint": [
                    {
                        "key": "cns-valid",
                        "severity": "error",
                        "human": "CNS deve ter 15 dígitos numéricos",
                        "expression": "matches('^[0-9]{15}$')"
                    }
                ]
            },
            # Nome
            {
                "id": "Patient.name",
                "path": "Patient.name",
                "min": 1,
                "max": "*"
            },
            {
                "id": "Patient.name.use",
                "path": "Patient.name.use",
                "min": 1,
                "binding": {
                    "strength": "required",
                    "valueSet": "http://hl7.org/fhir/ValueSet/name-use"
                }
            },
            {
                "id": "Patient.name.text",
                "path": "Patient.name.text",
                "short": "Nome completo",
                "min": 1
            },
            # Gênero
            {
                "id": "Patient.gender",
                "path": "Patient.gender",
                "min": 1,
                "binding": {
                    "strength": "required",
                    "valueSet": "http://hl7.org/fhir/ValueSet/administrative-gender"
                }
            },
            # Data de nascimento
            {
                "id": "Patient.birthDate",
                "path": "Patient.birthDate",
                "min": 1
            },
            # Extensões brasileiras
            {
                "id": "Patient.extension",
                "path": "Patient.extension",
                "slicing": {
                    "discriminator": [
                        {
                            "type": "value",
                            "path": "url"
                        }
                    ],
                    "rules": "open"
                }
            },
            {
                "id": "Patient.extension:raca",
                "path": "Patient.extension",
                "sliceName": "raca",
                "short": "Raça/Cor",
                "min": 0,
                "max": "1",
                "type": [
                    {
                        "code": "Extension",
                        "profile": [
                            "http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRRacaCorEtnia-1.0"
                        ]
                    }
                ]
            },
            {
                "id": "Patient.extension:nacionalidade",
                "path": "Patient.extension",
                "sliceName": "nacionalidade",
                "short": "Nacionalidade",
                "min": 0,
                "max": "1",
                "type": [
                    {
                        "code": "Extension",
                        "profile": [
                            "http://rnds.saude.gov.br/fhir/r4/StructureDefinition/BRNacionalidade"
                        ]
                    }
                ]
            },
            # Endereço
            {
                "id": "Patient.address",
                "path": "Patient.address",
                "min": 0,
                "max": "*"
            },
            {
                "id": "Patient.address.postalCode",
                "path": "Patient.address.postalCode",
                "short": "CEP",
                "constraint": [
                    {
                        "key": "cep-valid",
                        "severity": "warning",
                        "human": "CEP deve ter 8 dígitos",
                        "expression": "matches('^[0-9]{8}$')"
                    }
                ]
            },
            {
                "id": "Patient.address.country",
                "path": "Patient.address.country",
                "short": "País (ISO 3166-1 alpha-2)",
                "binding": {
                    "strength": "required",
                    "valueSet": "http://hl7.org/fhir/ValueSet/iso3166-1-2"
                }
            },
            # Contato
            {
                "id": "Patient.telecom",
                "path": "Patient.telecom",
                "min": 0,
                "max": "*"
            },
            {
                "id": "Patient.telecom.system",
                "path": "Patient.telecom.system",
                "min": 1,
                "binding": {
                    "strength": "required",
                    "valueSet": "http://hl7.org/fhir/ValueSet/contact-point-system"
                }
            },
            {
                "id": "Patient.telecom.value",
                "path": "Patient.telecom.value",
                "min": 1
            }
        ]
    }
}


# ValueSet para raça/cor brasileira
RACA_COR_VALUESET = {
    "resourceType": "ValueSet",
    "id": "BRRacaCor",
    "url": "http://openehrcore.com.br/fhir/ValueSet/BRRacaCor",
    "version": "1.0.0",
    "name": "BRRacaCor",
    "title": "Raça/Cor - Brasil",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Códigos de raça/cor conforme IBGE",
    "compose": {
        "include": [
            {
                "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor",
                "concept": [
                    {"code": "01", "display": "Branca"},
                    {"code": "02", "display": "Preta"},
                    {"code": "03", "display": "Parda"},
                    {"code": "04", "display": "Amarela"},
                    {"code": "05", "display": "Indígena"},
                    {"code": "99", "display": "Sem informação"}
                ]
            }
        ]
    }
}


# CodeSystem para raça/cor
RACA_COR_CODESYSTEM = {
    "resourceType": "CodeSystem",
    "id": "BRRacaCor",
    "url": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRRacaCor",
    "version": "1.0.0",
    "name": "BRRacaCor",
    "title": "Raça/Cor - Brasil (IBGE)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "Ministério da Saúde",
    "description": "Códigos de raça/cor conforme classificação IBGE",
    "caseSensitive": True,
    "content": "complete",
    "count": 6,
    "concept": [
        {"code": "01", "display": "Branca", "definition": "Pessoa que se autodeclara branca"},
        {"code": "02", "display": "Preta", "definition": "Pessoa que se autodeclara preta"},
        {"code": "03", "display": "Parda", "definition": "Pessoa que se autodeclara parda"},
        {"code": "04", "display": "Amarela", "definition": "Pessoa que se autodeclara amarela"},
        {"code": "05", "display": "Indígena", "definition": "Pessoa que se autodeclara indígena"},
        {"code": "99", "display": "Sem informação", "definition": "Informação não disponível"}
    ]
}
