"""
FHIR StructureDefinition - Organization BR (RNDS)

Perfil brasileiro para Organization baseado em:
- https://rnds-fhir.saude.gov.br/
- https://simplifier.net/redenacionaldedadosemsaude

Sprint 36: Conformidade RNDS
"""

ORGANIZATION_BR_PROFILE = {
    "resourceType": "StructureDefinition",
    "id": "BREstabelecimentoSaude-1.0",
    "url": "http://openehrcore.com.br/fhir/StructureDefinition/BREstabelecimentoSaude",
    "version": "1.0.0",
    "name": "BREstabelecimentoSaude",
    "title": "Estabelecimento de Saúde (Organization BR)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Perfil brasileiro para Organization, compatível com RNDS",
    "fhirVersion": "4.0.1",
    "kind": "resource",
    "abstract": False,
    "type": "Organization",
    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Organization",
    "derivation": "constraint",
    "differential": {
        "element": [
            {
                "id": "Organization",
                "path": "Organization",
                "short": "Estabelecimento de saúde no contexto brasileiro",
                "definition": "Organização com identificadores brasileiros (CNES, CNPJ)"
            },
            # Identifier - slicing
            {
                "id": "Organization.identifier",
                "path": "Organization.identifier",
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
            # CNES (obrigatório para estabelecimentos de saúde)
            {
                "id": "Organization.identifier:cnes",
                "path": "Organization.identifier",
                "sliceName": "cnes",
                "short": "CNES do estabelecimento",
                "definition": "Cadastro Nacional de Estabelecimentos de Saúde",
                "min": 1,
                "max": "1"
            },
            {
                "id": "Organization.identifier:cnes.system",
                "path": "Organization.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cnes"
            },
            {
                "id": "Organization.identifier:cnes.value",
                "path": "Organization.identifier.value",
                "min": 1,
                "constraint": [
                    {
                        "key": "cnes-valid",
                        "severity": "error",
                        "human": "CNES deve ter 7 dígitos numéricos",
                        "expression": "matches('^[0-9]{7}$')"
                    }
                ]
            },
            # CNPJ
            {
                "id": "Organization.identifier:cnpj",
                "path": "Organization.identifier",
                "sliceName": "cnpj",
                "short": "CNPJ da organização",
                "min": 0,
                "max": "1"
            },
            {
                "id": "Organization.identifier:cnpj.system",
                "path": "Organization.identifier.system",
                "min": 1,
                "fixedUri": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cnpj"
            },
            {
                "id": "Organization.identifier:cnpj.value",
                "path": "Organization.identifier.value",
                "min": 1,
                "constraint": [
                    {
                        "key": "cnpj-valid",
                        "severity": "error",
                        "human": "CNPJ deve ter 14 dígitos numéricos",
                        "expression": "matches('^[0-9]{14}$')"
                    }
                ]
            },
            # Active
            {
                "id": "Organization.active",
                "path": "Organization.active",
                "min": 1
            },
            # Type (tipo de estabelecimento)
            {
                "id": "Organization.type",
                "path": "Organization.type",
                "min": 1,
                "max": "*",
                "binding": {
                    "strength": "extensible",
                    "valueSet": "http://openehrcore.com.br/fhir/ValueSet/BRTipoEstabelecimentoSaude"
                }
            },
            # Name
            {
                "id": "Organization.name",
                "path": "Organization.name",
                "short": "Nome fantasia ou razão social",
                "min": 1
            },
            # Alias (nome fantasia)
            {
                "id": "Organization.alias",
                "path": "Organization.alias",
                "short": "Nome fantasia (se diferente da razão social)",
                "min": 0,
                "max": "*"
            },
            # Address
            {
                "id": "Organization.address",
                "path": "Organization.address",
                "min": 1,
                "max": "*"
            },
            {
                "id": "Organization.address.line",
                "path": "Organization.address.line",
                "short": "Logradouro, número, complemento",
                "min": 1
            },
            {
                "id": "Organization.address.city",
                "path": "Organization.address.city",
                "short": "Município (código IBGE recomendado)",
                "min": 1
            },
            {
                "id": "Organization.address.state",
                "path": "Organization.address.state",
                "short": "UF (sigla de 2 letras)",
                "min": 1,
                "constraint": [
                    {
                        "key": "uf-valid",
                        "severity": "error",
                        "human": "UF deve ter 2 letras maiúsculas",
                        "expression": "matches('^[A-Z]{2}$')"
                    }
                ]
            },
            {
                "id": "Organization.address.postalCode",
                "path": "Organization.address.postalCode",
                "short": "CEP",
                "min": 1,
                "constraint": [
                    {
                        "key": "cep-valid",
                        "severity": "error",
                        "human": "CEP deve ter 8 dígitos",
                        "expression": "matches('^[0-9]{8}$')"
                    }
                ]
            },
            {
                "id": "Organization.address.country",
                "path": "Organization.address.country",
                "short": "País (BR para Brasil)",
                "min": 1,
                "fixedString": "BR"
            },
            # Contact
            {
                "id": "Organization.telecom",
                "path": "Organization.telecom",
                "min": 0,
                "max": "*"
            },
            # Part Of (organização hierarquicamente superior)
            {
                "id": "Organization.partOf",
                "path": "Organization.partOf",
                "short": "Organização mãe (ex: Secretaria de Saúde)",
                "type": [
                    {
                        "code": "Reference",
                        "targetProfile": [
                            "http://openehrcore.com.br/fhir/StructureDefinition/BREstabelecimentoSaude"
                        ]
                    }
                ]
            }
        ]
    }
}


# ValueSet para tipos de estabelecimento de saúde
TIPO_ESTABELECIMENTO_VALUESET = {
    "resourceType": "ValueSet",
    "id": "BRTipoEstabelecimentoSaude",
    "url": "http://openehrcore.com.br/fhir/ValueSet/BRTipoEstabelecimentoSaude",
    "version": "1.0.0",
    "name": "BRTipoEstabelecimentoSaude",
    "title": "Tipo de Estabelecimento de Saúde - Brasil",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "OpenEHRCore",
    "description": "Tipos de estabelecimentos de saúde conforme CNES",
    "compose": {
        "include": [
            {
                "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoEstabelecimentoSaude",
                "concept": [
                    {"code": "01", "display": "Posto de Saúde"},
                    {"code": "02", "display": "Centro de Saúde/Unidade Básica de Saúde"},
                    {"code": "04", "display": "Policlínica"},
                    {"code": "05", "display": "Hospital Geral"},
                    {"code": "07", "display": "Hospital Especializado"},
                    {"code": "15", "display": "Unidade Mista"},
                    {"code": "20", "display": "Pronto Socorro Geral"},
                    {"code": "21", "display": "Pronto Socorro Especializado"},
                    {"code": "22", "display": "Consultório Isolado"},
                    {"code": "32", "display": "Unidade Móvel Fluvial"},
                    {"code": "36", "display": "Clínica/Centro de Especialidades"},
                    {"code": "39", "display": "Unidade de Apoio Diagnose e Terapia (SADT Isolado)"},
                    {"code": "40", "display": "Unidade Móvel Terrestre"},
                    {"code": "42", "display": "Unidade Móvel de Nível Pré-Hospitalar na Área de Urgência"},
                    {"code": "43", "display": "Farmácia"},
                    {"code": "50", "display": "Unidade de Vigilância em Saúde"},
                    {"code": "60", "display": "Cooperativa ou Empresa de Cessão de Trabalhadores na Saúde"},
                    {"code": "61", "display": "Centro de Parto Normal - Isolado"},
                    {"code": "62", "display": "Hospital/Dia - Isolado"},
                    {"code": "64", "display": "Central de Regulação de Serviços de Saúde"},
                    {"code": "67", "display": "Laboratório Central de Saúde Pública - LACEN"},
                    {"code": "68", "display": "Central de Gestão em Saúde"},
                    {"code": "69", "display": "Centro de Atenção Hemoterapia e/ou Hematológica"},
                    {"code": "70", "display": "Centro de Atenção Psicossocial"},
                    {"code": "71", "display": "Centro de Apoio à Saúde da Família"},
                    {"code": "72", "display": "Unidade de Atenção à Saúde Indígena"},
                    {"code": "73", "display": "Pronto Atendimento"},
                    {"code": "74", "display": "Polo Academia da Saúde"},
                    {"code": "75", "display": "Telessaúde"},
                    {"code": "76", "display": "Central de Regulação Médica das Urgências"},
                    {"code": "77", "display": "Serviço de Atenção Domiciliar Isolado (Home Care)"},
                    {"code": "79", "display": "Oficina Ortopédica"},
                    {"code": "80", "display": "Laboratório de Saúde Pública"},
                    {"code": "81", "display": "Central de Regulação do Acesso"},
                    {"code": "82", "display": "Central de Notificação, Captação e Distribuição de Órgãos Estadual"},
                    {"code": "83", "display": "Polo de Prevenção de Doenças e Agravos e Promoção da Saúde"},
                    {"code": "84", "display": "Central de Abastecimento"},
                    {"code": "85", "display": "Centro de Imunização"},
                    {"code": "86", "display": "Central de Regulação Hospitalar"},
                    {"code": "87", "display": "Unidade de Saúde da Família"}
                ]
            }
        ]
    }
}


# CodeSystem para tipos de estabelecimento
TIPO_ESTABELECIMENTO_CODESYSTEM = {
    "resourceType": "CodeSystem",
    "id": "BRTipoEstabelecimentoSaude",
    "url": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoEstabelecimentoSaude",
    "version": "1.0.0",
    "name": "BRTipoEstabelecimentoSaude",
    "title": "Tipo de Estabelecimento de Saúde - Brasil (CNES)",
    "status": "active",
    "experimental": False,
    "date": "2024-12-01",
    "publisher": "Ministério da Saúde",
    "description": "Tipos de estabelecimentos de saúde conforme classificação CNES",
    "caseSensitive": True,
    "content": "complete",
    "count": 42
}
