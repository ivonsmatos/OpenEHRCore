"""
HealthStack - Seed Data Script
Creates sample data in HAPI FHIR for development and testing.

Run with: python manage.py runscript seed_fhir_data
Or directly: python scripts/seed_fhir_data.py
"""

import requests
import json
import sys
from datetime import datetime, timedelta

FHIR_URL = "http://localhost:8080/fhir"
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

# Track created IDs for references
created_ids = {
    "practitioners": [],
    "patients": [],
    "organizations": []
}


def check_fhir_available():
    """Check if HAPI FHIR is available"""
    try:
        response = requests.get(f"{FHIR_URL}/metadata", timeout=5)
        return response.status_code == 200
    except:
        return False


def create_resource(resource_type, resource_data):
    """Create a FHIR resource and return the created ID"""
    try:
        # Remove id field to let FHIR generate it
        if 'id' in resource_data:
            del resource_data['id']
            
        response = requests.post(
            f"{FHIR_URL}/{resource_type}",
            json=resource_data,
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            resource_id = result.get('id')
            print(f"  ✓ {resource_type} created: ID={resource_id}")
            return resource_id
        else:
            print(f"  ✗ Failed to create {resource_type}: {response.status_code}")
            print(f"    {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ✗ Error creating {resource_type}: {e}")
        return None


def seed_organizations():
    """Create sample organizations"""
    print("\n📋 Creating Organizations...")
    
    orgs = [
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider"
                }]
            }],
            "name": "HealthStack Hospital Central",
            "telecom": [
                {"system": "phone", "value": "(11) 3000-0000", "use": "work"},
                {"system": "email", "value": "contato@healthstack.com", "use": "work"}
            ],
            "address": [{
                "use": "work",
                "line": ["Av. Paulista, 1500"],
                "city": "São Paulo",
                "state": "SP",
                "postalCode": "01310-200",
                "country": "BR"
            }]
        },
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "dept",
                    "display": "Hospital Department"
                }]
            }],
            "name": "Departamento de Cardiologia"
        }
    ]
    
    for org in orgs:
        org_id = create_resource("Organization", org)
        if org_id:
            created_ids["organizations"].append(org_id)


def seed_practitioners():
    """Create sample practitioners"""
    print("\n👨‍⚕️ Creating Practitioners...")
    
    practitioners = [
        {
            "resourceType": "Practitioner",
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
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "123.456.789-00"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": "CRM-SP 123456"}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": "cardiology", "display": "Cardiologia"}],
                    "text": "Cardiologia"
                }
            }],
            "telecom": [
                {"system": "phone", "value": "(11) 99999-0001", "use": "mobile"},
                {"system": "email", "value": "maria.silva@healthstack.com", "use": "work"}
            ]
        },
        {
            "resourceType": "Practitioner",
            "active": True,
            "name": [{"use": "official", "family": "Santos", "given": ["João", "Pedro"], "prefix": ["Dr."]}],
            "gender": "male",
            "birthDate": "1978-07-20",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "987.654.321-00"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": "CRM-SP 654321"}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": "orthopedics", "display": "Ortopedia"}],
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
            "active": True,
            "name": [{"use": "official", "family": "Oliveira", "given": ["Ana", "Beatriz"], "prefix": ["Dra."]}],
            "gender": "female",
            "birthDate": "1990-11-08",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "456.789.123-00"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": "CRM-SP 789123"}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": "pediatrics", "display": "Pediatria"}],
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
            "active": True,
            "name": [{"use": "official", "family": "Costa", "given": ["Roberto"], "prefix": ["Dr."]}],
            "gender": "male",
            "birthDate": "1982-04-25",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "321.654.987-00"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": "CRM-SP 456789"}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": "neurology", "display": "Neurologia"}],
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
            "active": True,
            "name": [{"use": "official", "family": "Ferreira", "given": ["Patricia"], "prefix": ["Dra."]}],
            "gender": "female",
            "birthDate": "1988-09-12",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "789.123.456-00"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": "CRM-SP 321654"}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": "dermatology", "display": "Dermatologia"}],
                    "text": "Dermatologia"
                }
            }],
            "telecom": [
                {"system": "phone", "value": "(11) 99999-0005", "use": "mobile"},
                {"system": "email", "value": "patricia.ferreira@healthstack.com", "use": "work"}
            ]
        }
    ]
    
    for p in practitioners:
        pid = create_resource("Practitioner", p)
        if pid:
            created_ids["practitioners"].append(pid)


def seed_patients():
    """Create sample patients"""
    print("\n🏥 Creating Patients...")
    
    patients = [
        {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": "Souza", "given": ["Carlos", "Eduardo"]}],
            "gender": "male",
            "birthDate": "1975-06-15",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "111.222.333-44"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns", "value": "123456789012345"}
            ],
            "telecom": [
                {"system": "phone", "value": "(11) 98888-0001", "use": "mobile"},
                {"system": "email", "value": "carlos.souza@email.com", "use": "home"}
            ],
            "address": [{
                "use": "home",
                "line": ["Rua das Flores, 123"],
                "city": "São Paulo",
                "state": "SP",
                "postalCode": "01234-567",
                "country": "BR"
            }],
            "maritalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "M", "display": "Married"}]
            }
        },
        {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": "Lima", "given": ["Fernanda"]}],
            "gender": "female",
            "birthDate": "1992-03-22",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "222.333.444-55"},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns", "value": "234567890123456"}
            ],
            "telecom": [
                {"system": "phone", "value": "(11) 98888-0002", "use": "mobile"},
                {"system": "email", "value": "fernanda.lima@email.com", "use": "home"}
            ],
            "address": [{
                "use": "home",
                "line": ["Av. Brasil, 456"],
                "city": "São Paulo",
                "state": "SP",
                "postalCode": "02345-678",
                "country": "BR"
            }]
        },
        {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": "Pereira", "given": ["Ricardo"]}],
            "gender": "male",
            "birthDate": "1988-11-10",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "333.444.555-66"}
            ],
            "telecom": [
                {"system": "phone", "value": "(11) 98888-0003", "use": "mobile"}
            ],
            "address": [{
                "use": "home",
                "line": ["Rua Augusta, 789"],
                "city": "São Paulo",
                "state": "SP",
                "postalCode": "03456-789",
                "country": "BR"
            }]
        },
        {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": "Almeida", "given": ["Julia", "Maria"]}],
            "gender": "female",
            "birthDate": "2015-08-05",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "444.555.666-77"}
            ],
            "telecom": [
                {"system": "phone", "value": "(11) 98888-0004", "use": "mobile"}
            ]
        },
        {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": "Martins", "given": ["Antonio"]}],
            "gender": "male",
            "birthDate": "1955-02-28",
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": "555.666.777-88"}
            ],
            "telecom": [
                {"system": "phone", "value": "(11) 98888-0005", "use": "mobile"}
            ]
        }
    ]
    
    for p in patients:
        pid = create_resource("Patient", p)
        if pid:
            created_ids["patients"].append(pid)


def seed_observations(patient_ids):
    """Create sample observations (vital signs) for patients"""
    print("\n📊 Creating Observations (Vital Signs)...")
    
    if not patient_ids:
        print("  ⚠ No patients to create observations for")
        return
    
    vital_signs = [
        {"code": "8867-4", "display": "Heart rate", "unit": "/min", "values": [72, 78, 65, 80, 75]},
        {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg", "values": [120, 130, 118, 140, 125]},
        {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg", "values": [80, 85, 75, 90, 82]},
        {"code": "8310-5", "display": "Body temperature", "unit": "Cel", "values": [36.5, 37.0, 36.8, 37.5, 36.6]},
        {"code": "9279-1", "display": "Respiratory rate", "unit": "/min", "values": [16, 18, 14, 20, 17]}
    ]
    
    for i, patient_id in enumerate(patient_ids[:3]):  # Only first 3 patients
        for vital in vital_signs:
            observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": vital["code"],
                        "display": vital["display"]
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": (datetime.now() - timedelta(days=i)).isoformat(),
                "valueQuantity": {
                    "value": vital["values"][i % len(vital["values"])],
                    "unit": vital["unit"],
                    "system": "http://unitsofmeasure.org",
                    "code": vital["unit"]
                }
            }
            create_resource("Observation", observation)


def seed_conditions(patient_ids):
    """Create sample conditions (diagnoses) for patients"""
    print("\n🩺 Creating Conditions...")
    
    if not patient_ids:
        print("  ⚠ No patients to create conditions for")
        return
    
    conditions = [
        {"code": "38341003", "display": "Hipertensão arterial", "status": "active"},
        {"code": "73211009", "display": "Diabetes mellitus tipo 2", "status": "active"},
        {"code": "195967001", "display": "Asma", "status": "resolved"},
        {"code": "49436004", "display": "Fibrilação atrial", "status": "active"},
        {"code": "13644009", "display": "Hipotireoidismo", "status": "active"}
    ]
    
    for i, patient_id in enumerate(patient_ids):
        condition_data = conditions[i % len(conditions)]
        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": condition_data["status"]
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": condition_data["code"],
                    "display": condition_data["display"]
                }],
                "text": condition_data["display"]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "onsetDateTime": (datetime.now() - timedelta(days=365)).isoformat()
        }
        create_resource("Condition", condition)


def run():
    """Main entry point for Django runscript"""
    main()


def main():
    """Main function to seed all data"""
    print("=" * 60)
    print("🏥 HealthStack FHIR Seed Data")
    print("=" * 60)
    
    # Check FHIR availability
    print("\n🔍 Checking HAPI FHIR availability...")
    if not check_fhir_available():
        print("  ✗ HAPI FHIR is not available at", FHIR_URL)
        print("  Please ensure HAPI FHIR is running and try again.")
        sys.exit(1)
    print("  ✓ HAPI FHIR is available")
    
    # Seed all data
    seed_organizations()
    seed_practitioners()
    seed_patients()
    seed_observations(created_ids["patients"])
    seed_conditions(created_ids["patients"])
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  Organizations: {len(created_ids['organizations'])}")
    print(f"  Practitioners: {len(created_ids['practitioners'])}")
    print(f"  Patients: {len(created_ids['patients'])}")
    print("=" * 60)
    print("✅ Seed data completed!")


if __name__ == "__main__":
    main()
