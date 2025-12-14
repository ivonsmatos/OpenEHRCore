"""
Script para criar profissionais de exemplo no HAPI FHIR
Execute: python manage.py shell < create_sample_practitioners.py
"""

import requests
import json

FHIR_URL = "http://localhost:8080/fhir"

practitioners = [
    {
        "resourceType": "Practitioner",
        "id": "1",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Silva",
            "given": ["Maria", "Carolina"],
            "prefix": ["Dra."]
        }],
        "gender": "female",
        "birthDate": "1985-03-15",
        "identifier": [
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "123.456.789-00"
            },
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP 123456"
            }
        ],
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty",
                    "code": "cardiology",
                    "display": "Cardiologia"
                }],
                "text": "Cardiologia"
            }
        }],
        "telecom": [
            {"system": "phone", "value": "(11) 99999-0001", "use": "mobile"},
            {"system": "email", "value": "maria.silva@healthstack.com", "use": "work"}
        ],
        "address": [{
            "use": "work",
            "line": ["Av. Paulista, 1000"],
            "city": "São Paulo",
            "state": "SP",
            "postalCode": "01310-100",
            "country": "BR"
        }]
    },
    {
        "resourceType": "Practitioner",
        "id": "2",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Santos",
            "given": ["João", "Pedro"],
            "prefix": ["Dr."]
        }],
        "gender": "male",
        "birthDate": "1978-07-20",
        "identifier": [
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "987.654.321-00"
            },
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP 654321"
            }
        ],
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty",
                    "code": "orthopedics",
                    "display": "Ortopedia"
                }],
                "text": "Ortopedia"
            }
        }],
        "telecom": [
            {"system": "phone", "value": "(11) 99999-0002", "use": "mobile"},
            {"system": "email", "value": "joao.santos@healthstack.com", "use": "work"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "3",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Oliveira",
            "given": ["Ana", "Beatriz"],
            "prefix": ["Dra."]
        }],
        "gender": "female",
        "birthDate": "1990-11-08",
        "identifier": [
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "456.789.123-00"
            },
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP 789123"
            }
        ],
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty",
                    "code": "pediatrics",
                    "display": "Pediatria"
                }],
                "text": "Pediatria"
            }
        }],
        "telecom": [
            {"system": "phone", "value": "(11) 99999-0003", "use": "mobile"},
            {"system": "email", "value": "ana.oliveira@healthstack.com", "use": "work"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "4",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Costa",
            "given": ["Roberto"],
            "prefix": ["Dr."]
        }],
        "gender": "male",
        "birthDate": "1982-04-25",
        "identifier": [
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "321.654.987-00"
            },
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP 456789"
            }
        ],
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty",
                    "code": "neurology",
                    "display": "Neurologia"
                }],
                "text": "Neurologia"
            }
        }],
        "telecom": [
            {"system": "phone", "value": "(11) 99999-0004", "use": "mobile"},
            {"system": "email", "value": "roberto.costa@healthstack.com", "use": "work"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "5",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Ferreira",
            "given": ["Patricia"],
            "prefix": ["Dra."]
        }],
        "gender": "female",
        "birthDate": "1988-09-12",
        "identifier": [
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                "value": "789.123.456-00"
            },
            {
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP 321654"
            }
        ],
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty",
                    "code": "dermatology",
                    "display": "Dermatologia"
                }],
                "text": "Dermatologia"
            }
        }],
        "telecom": [
            {"system": "phone", "value": "(11) 99999-0005", "use": "mobile"},
            {"system": "email", "value": "patricia.ferreira@healthstack.com", "use": "work"}
        ]
    }
]

def create_practitioners():
    headers = {"Content-Type": "application/fhir+json"}
    
    for p in practitioners:
        pid = p.get("id")
        url = f"{FHIR_URL}/Practitioner/{pid}"
        
        try:
            # Use PUT to create with specific ID
            response = requests.put(url, json=p, headers=headers)
            if response.status_code in [200, 201]:
                print(f"✓ Practitioner {pid} criado/atualizado: {p['name'][0]['given'][0]} {p['name'][0]['family']}")
            else:
                print(f"✗ Erro ao criar Practitioner {pid}: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"✗ Erro de conexão para Practitioner {pid}: {e}")

if __name__ == "__main__":
    print("Criando profissionais de exemplo no HAPI FHIR...")
    print("=" * 50)
    create_practitioners()
    print("=" * 50)
    print("Concluído!")
