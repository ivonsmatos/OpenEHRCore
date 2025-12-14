"""
Direct HAPI FHIR Data Seed Script
Bypasses Django API and writes directly to HAPI FHIR

Creates 50 patients with complete FHIR data
"""

import requests
import random
from datetime import datetime, timedelta
import time
import json

# Configuration
FHIR_URL = "http://localhost:8080/fhir"

# Brazilian names
FIRST_NAMES_M = ["João", "Pedro", "Lucas", "Matheus", "Gabriel", "Rafael", "Bruno", "Carlos", "André", "Felipe",
                 "Marcos", "Paulo", "Ricardo", "Fernando", "Eduardo", "Gustavo", "Rodrigo", "Alexandre", "Thiago", "Leonardo"]
FIRST_NAMES_F = ["Maria", "Ana", "Julia", "Beatriz", "Larissa", "Camila", "Fernanda", "Amanda", "Carolina", "Patricia",
                 "Gabriela", "Leticia", "Mariana", "Isabela", "Bruna", "Juliana", "Aline", "Vanessa", "Renata", "Priscila"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes"]

SPECIALTIES = ["Cardiologia", "Neurologia", "Ortopedia", "Pediatria", "Ginecologia", "Dermatologia", "Oftalmologia", "Psiquiatria"]

ICD10_CODES = [
    {"code": "I10", "display": "Hipertensao essencial"},
    {"code": "E11.9", "display": "Diabetes mellitus tipo 2"},
    {"code": "J06.9", "display": "Infeccao respiratoria"},
    {"code": "K21.0", "display": "Doenca do refluxo"},
    {"code": "M54.5", "display": "Dor lombar"},
]

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/fhir+json',
    'Accept': 'application/fhir+json'
})

def generate_cpf():
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])

def random_date(start_year=1950, end_year=2005):
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"

def create_patient(i, first_name, last_name, gender, birth_date):
    """Create FHIR Patient resource."""
    patient = {
        "resourceType": "Patient",
        "identifier": [{
            "use": "official",
            "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "TAX"}]},
            "system": "http://openehrcore.com.br/cpf",
            "value": generate_cpf()
        }],
        "active": True,
        "name": [{
            "use": "official",
            "family": last_name,
            "given": [first_name]
        }],
        "telecom": [
            {"system": "phone", "value": f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}", "use": "mobile"},
            {"system": "email", "value": f"{first_name.lower()}.{last_name.lower()}{i}@email.com"}
        ],
        "gender": gender,
        "birthDate": birth_date,
        "address": [{
            "use": "home",
            "type": "physical",
            "line": [f"Rua {random.choice(LAST_NAMES)}, {random.randint(1, 999)}"],
            "city": random.choice(["Sao Paulo", "Campinas", "Santos"]),
            "state": "SP",
            "postalCode": f"{random.randint(1000, 9999):05d}-{random.randint(0, 999):03d}",
            "country": "BR"
        }],
        "maritalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": random.choice(["S", "M", "D", "W"])
            }]
        }
    }
    
    response = session.post(f"{FHIR_URL}/Patient", json=patient)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"  Error creating patient: {response.status_code}")
        return None

def create_practitioner(i, first_name, last_name, gender, specialty):
    """Create FHIR Practitioner resource."""
    practitioner = {
        "resourceType": "Practitioner",
        "identifier": [{
            "system": "http://www.cremesp.org.br",
            "value": f"CRM-SP-{random.randint(100000, 999999)}"
        }],
        "active": True,
        "name": [{
            "use": "official",
            "prefix": ["Dr."] if i < 10 else [],
            "family": last_name,
            "given": [first_name]
        }],
        "telecom": [
            {"system": "email", "value": f"{first_name.lower()}.{last_name.lower()}@hospital.com"}
        ],
        "gender": gender,
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                    "code": "MD",
                    "display": specialty
                }]
            }
        }]
    }
    
    response = session.post(f"{FHIR_URL}/Practitioner", json=practitioner)
    if response.status_code == 201:
        return response.json()
    return None

def create_condition(patient_id, icd_code):
    """Create FHIR Condition resource."""
    condition = {
        "resourceType": "Condition",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": random.choice(["active", "resolved", "remission"])
            }]
        },
        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed"
            }]
        },
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": "encounter-diagnosis"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://hl7.org/fhir/sid/icd-10",
                "code": icd_code["code"],
                "display": icd_code["display"]
            }]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "onsetDateTime": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
    }
    
    response = session.post(f"{FHIR_URL}/Condition", json=condition)
    return response.status_code == 201

def create_observation(patient_id, code, display, value, unit):
    """Create FHIR Observation (vital sign)."""
    observation = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": code,
                "display": display
            }]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valueQuantity": {
            "value": value,
            "unit": unit,
            "system": "http://unitsofmeasure.org"
        }
    }
    
    response = session.post(f"{FHIR_URL}/Observation", json=observation)
    return response.status_code == 201

def create_appointment(patient_id, practitioner_id):
    """Create FHIR Appointment."""
    days_offset = random.randint(-30, 30)
    start = datetime.now() + timedelta(days=days_offset, hours=random.randint(8, 17))
    
    appointment = {
        "resourceType": "Appointment",
        "status": random.choice(["booked", "fulfilled", "cancelled"]) if days_offset < 0 else "booked",
        "serviceCategory": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/service-category",
                "code": "17",
                "display": "General Practice"
            }]
        }],
        "serviceType": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/service-type",
                "code": "124",
                "display": random.choice(SPECIALTIES)
            }]
        }],
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": (start + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "participant": [
            {"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"},
            {"actor": {"reference": f"Practitioner/{practitioner_id}"}, "status": "accepted"} if practitioner_id else None
        ]
    }
    
    # Remove None participants
    appointment["participant"] = [p for p in appointment["participant"] if p]
    
    response = session.post(f"{FHIR_URL}/Appointment", json=appointment)
    return response.status_code == 201

def create_allergy(patient_id, substance):
    """Create FHIR AllergyIntolerance."""
    allergy = {
        "resourceType": "AllergyIntolerance",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "active"
            }]
        },
        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                "code": "confirmed"
            }]
        },
        "type": "allergy",
        "category": ["medication"],
        "criticality": random.choice(["low", "high"]),
        "code": {"text": substance},
        "patient": {"reference": f"Patient/{patient_id}"},
        "recordedDate": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = session.post(f"{FHIR_URL}/AllergyIntolerance", json=allergy)
    return response.status_code == 201

def main():
    print("=" * 60)
    print("🏥 Direct HAPI FHIR Data Seed")
    print("=" * 60)
    
    # Test connection
    response = session.get(f"{FHIR_URL}/metadata")
    if response.status_code != 200:
        print(f"❌ Cannot connect to FHIR server: {response.status_code}")
        return
    print("✅ Connected to HAPI FHIR")
    
    patient_ids = []
    practitioner_ids = []
    
    # Create 20 practitioners
    print("\n📋 Creating 20 practitioners...")
    for i in range(20):
        gender = random.choice(["male", "female"])
        first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        specialty = random.choice(SPECIALTIES)
        
        result = create_practitioner(i, first_name, last_name, gender, specialty)
        if result:
            practitioner_ids.append(result["id"])
            print(f"  ✅ Practitioner {i+1}: Dr. {first_name} {last_name}")
        time.sleep(0.1)
    
    # Create 50 patients
    print("\n📋 Creating 50 patients...")
    for i in range(50):
        gender = random.choice(["male", "female"])
        first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        birth_date = random_date()
        
        result = create_patient(i, first_name, last_name, gender, birth_date)
        if result:
            patient_ids.append(result["id"])
            print(f"  ✅ Patient {i+1}: {first_name} {last_name}")
        time.sleep(0.1)
    
    # Create conditions for patients
    print("\n📋 Creating conditions...")
    conditions_count = 0
    for patient_id in patient_ids:
        for _ in range(random.randint(1, 3)):
            if create_condition(patient_id, random.choice(ICD10_CODES)):
                conditions_count += 1
        time.sleep(0.05)
    print(f"  ✅ Created {conditions_count} conditions")
    
    # Create vital signs
    print("\n📋 Creating vital signs...")
    vitals = [
        ("8867-4", "Heart rate", 60, 100, "beats/min"),
        ("8480-6", "Systolic BP", 110, 140, "mmHg"),
        ("8462-4", "Diastolic BP", 70, 90, "mmHg"),
        ("8310-5", "Body temperature", 36.0, 37.5, "Cel"),
        ("2708-6", "SpO2", 95, 100, "%"),
    ]
    vitals_count = 0
    for patient_id in patient_ids:
        for code, display, min_val, max_val, unit in vitals:
            if create_observation(patient_id, code, display, round(random.uniform(min_val, max_val), 1), unit):
                vitals_count += 1
        time.sleep(0.05)
    print(f"  ✅ Created {vitals_count} vital signs")
    
    # Create appointments
    print("\n📋 Creating appointments...")
    appointments_count = 0
    for patient_id in patient_ids:
        for _ in range(random.randint(1, 3)):
            pract_id = random.choice(practitioner_ids) if practitioner_ids else None
            if create_appointment(patient_id, pract_id):
                appointments_count += 1
        time.sleep(0.05)
    print(f"  ✅ Created {appointments_count} appointments")
    
    # Create allergies (30% of patients)
    print("\n📋 Creating allergies...")
    allergies_count = 0
    allergies = ["Penicilina", "Dipirona", "AAS", "Sulfa", "Iodo"]
    for patient_id in patient_ids:
        if random.random() < 0.3:
            if create_allergy(patient_id, random.choice(allergies)):
                allergies_count += 1
        time.sleep(0.02)
    print(f"  ✅ Created {allergies_count} allergies")
    
    print("\n" + "=" * 60)
    print("✅ Data seed complete!")
    print(f"   Practitioners: {len(practitioner_ids)}")
    print(f"   Patients: {len(patient_ids)}")
    print(f"   Conditions: {conditions_count}")
    print(f"   Vital Signs: {vitals_count}")
    print(f"   Appointments: {appointments_count}")
    print(f"   Allergies: {allergies_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
