"""
Comprehensive FHIR Data Seed Script
Sprint 30: Full System Population

Creates:
- 50 Patients with complete demographics
- 20 Practitioners (doctors, nurses, admins)
- Organization structure (hospital, departments)
- Locations (rooms, beds with all statuses)
- 100+ Appointments
- Conditions/Diagnoses per patient
- Medications/Prescriptions
- Vital Signs (Observations)
- Allergies
- Immunizations
- Encounters/Admissions
- Visitors
- Financial data (Coverage, Invoices)
"""

import requests
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "contato@ivonmatos.com.br"
PASSWORD = "Protonsysdba@1986"

# Brazilian names for realistic data
FIRST_NAMES_M = ["João", "Pedro", "Lucas", "Matheus", "Gabriel", "Rafael", "Bruno", "Carlos", "André", "Felipe",
                 "Marcos", "Paulo", "Ricardo", "Fernando", "Eduardo", "Gustavo", "Rodrigo", "Alexandre", "Thiago", "Leonardo"]
FIRST_NAMES_F = ["Maria", "Ana", "Julia", "Beatriz", "Larissa", "Camila", "Fernanda", "Amanda", "Carolina", "Patricia",
                 "Gabriela", "Leticia", "Mariana", "Isabela", "Bruna", "Juliana", "Aline", "Vanessa", "Renata", "Priscila"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
              "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa"]

# Medical data
SPECIALTIES = ["Cardiologia", "Neurologia", "Ortopedia", "Pediatria", "Ginecologia", "Dermatologia", 
               "Oftalmologia", "Psiquiatria", "Urologia", "Gastroenterologia"]
ICD10_CODES = [
    {"code": "I10", "display": "Hipertensão essencial (primária)"},
    {"code": "E11.9", "display": "Diabetes mellitus tipo 2 sem complicações"},
    {"code": "J06.9", "display": "Infecção aguda das vias aéreas superiores"},
    {"code": "K21.0", "display": "Doença do refluxo gastroesofágico com esofagite"},
    {"code": "M54.5", "display": "Dor lombar baixa"},
    {"code": "F32.0", "display": "Episódio depressivo leve"},
    {"code": "J45.0", "display": "Asma predominantemente alérgica"},
    {"code": "N39.0", "display": "Infecção do trato urinário"},
    {"code": "G43.9", "display": "Enxaqueca não especificada"},
    {"code": "L30.9", "display": "Dermatite não especificada"},
]
MEDICATIONS = [
    {"name": "Losartana 50mg", "rxcui": "979492"},
    {"name": "Metformina 850mg", "rxcui": "861007"},
    {"name": "Omeprazol 20mg", "rxcui": "313585"},
    {"name": "Atenolol 25mg", "rxcui": "197381"},
    {"name": "Sinvastatina 20mg", "rxcui": "312961"},
    {"name": "Dipirona 500mg", "rxcui": "1049635"},
    {"name": "Amoxicilina 500mg", "rxcui": "308182"},
    {"name": "Ibuprofeno 600mg", "rxcui": "310965"},
    {"name": "Fluoxetina 20mg", "rxcui": "310385"},
    {"name": "Loratadina 10mg", "rxcui": "311372"},
]
ALLERGIES = ["Penicilina", "Dipirona", "AAS", "Iodo", "Látex", "Sulfa", "Frutos do mar", "Amendoim", "Ovo", "Leite"]
VACCINES = [
    {"code": "08", "display": "Hepatite B"},
    {"code": "20", "display": "DTaP"},
    {"code": "03", "display": "MMR"},
    {"code": "21", "display": "Varicela"},
    {"code": "33", "display": "Pneumocócica"},
    {"code": "141", "display": "Influenza"},
    {"code": "207", "display": "COVID-19 Moderna"},
    {"code": "208", "display": "COVID-19 Pfizer"},
]
BED_STATUSES = ["available", "occupied", "reserved", "maintenance"]
APPOINTMENT_STATUSES = ["booked", "arrived", "fulfilled", "cancelled", "noshow"]

session = requests.Session()
token = None

def login():
    """Authenticate and get token."""
    global token
    response = session.post(f"{BASE_URL}/auth/login/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Login successful")
        return True
    print(f"❌ Login failed: {response.status_code}")
    return False

def generate_cpf():
    """Generate valid CPF."""
    cpf = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        val = sum((cpf[num] * ((len(cpf)+1) - num)) for num in range(len(cpf))) % 11
        cpf.append(11 - val if val > 1 else 0)
    return ''.join(map(str, cpf))

def generate_phone():
    """Generate Brazilian phone number."""
    return f"({random.randint(11,99)}) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def random_date(start_year=1950, end_year=2005):
    """Generate random birth date."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"

def create_organization():
    """Create hospital organization."""
    org = {
        "name": "Hospital HealthStack",
        "alias": ["HOC"],
        "type": "prov",
        "active": True,
        "address": {
            "city": "São Paulo",
            "state": "SP",
            "country": "BR"
        }
    }
    response = session.post(f"{BASE_URL}/organizations/", json=org)
    if response.status_code in [200, 201]:
        print("✅ Organization created")
        return response.json().get("id")
    print(f"⚠️ Organization: {response.status_code}")
    return None

def create_practitioners(count=20):
    """Create practitioners of various types."""
    practitioners = []
    roles = ["medico", "enfermeiro", "tecnico", "recepcionista", "admin"]
    
    for i in range(count):
        gender = random.choice(["male", "female"])
        first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        
        practitioner = {
            "name": f"Dr. {first_name} {last_name}" if i < 10 else f"{first_name} {last_name}",
            "gender": gender,
            "specialty": random.choice(SPECIALTIES) if i < 10 else None,
            "role": roles[i % len(roles)],
            "crm": f"CRM-SP {random.randint(100000, 999999)}" if i < 10 else None,
            "email": f"{first_name.lower()}.{last_name.lower()}@hospital.com",
            "phone": generate_phone(),
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/practitioners/", json=practitioner)
        if response.status_code in [200, 201]:
            practitioners.append(response.json())
            print(f"✅ Practitioner {i+1}/{count}: {practitioner['name']}")
        else:
            print(f"⚠️ Practitioner {i+1}: {response.status_code}")
    
    return practitioners

def create_locations(count=30):
    """Create rooms and beds."""
    locations = []
    departments = ["UTI", "Enfermaria", "Centro Cirúrgico", "Emergência", "Pediatria"]
    
    for i in range(count):
        dept = departments[i % len(departments)]
        bed_num = (i % 10) + 1
        status = random.choice(BED_STATUSES)
        
        location = {
            "name": f"Leito {dept}-{bed_num:02d}",
            "description": f"Leito {bed_num} do departamento de {dept}",
            "type": "bd",  # bed
            "status": status,
            "department": dept,
            "floor": (i // 10) + 1
        }
        
        # Create via IPD endpoint
        response = session.post(f"{BASE_URL}/ipd/beds/", json=location)
        if response.status_code in [200, 201]:
            locations.append(response.json())
            print(f"✅ Bed {i+1}/{count}: {location['name']} ({status})")
        else:
            print(f"⚠️ Bed {i+1}: {response.status_code}")
    
    return locations

def create_patients(count=50):
    """Create patients with complete data."""
    patients = []
    
    for i in range(count):
        gender = random.choice(["male", "female"])
        first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        
        patient = {
            "name": f"{first_name} {last_name}",
            "gender": gender,
            "birthDate": random_date(),
            "cpf": generate_cpf(),
            "phone": generate_phone(),
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "address": {
                "line": [f"Rua {random.choice(LAST_NAMES)}, {random.randint(1, 999)}"],
                "city": random.choice(["São Paulo", "Campinas", "Santos", "Guarulhos"]),
                "state": "SP",
                "postalCode": f"{random.randint(1000, 9999):05d}-{random.randint(0, 999):03d}",
                "country": "BR"
            },
            "maritalStatus": random.choice(["single", "married", "divorced", "widowed"]),
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/patients/", json=patient)
        if response.status_code in [200, 201]:
            patient_data = response.json()
            patients.append(patient_data)
            print(f"✅ Patient {i+1}/{count}: {patient['name']}")
        else:
            print(f"⚠️ Patient {i+1}: {response.status_code} - {response.text[:100]}")
    
    return patients

def create_conditions(patients, practitioners):
    """Create conditions/diagnoses for patients."""
    count = 0
    for patient in patients:
        # Each patient gets 1-3 conditions
        num_conditions = random.randint(1, 3)
        for _ in range(num_conditions):
            icd = random.choice(ICD10_CODES)
            condition = {
                "patient_id": patient.get("id"),
                "code": icd["code"],
                "display": icd["display"],
                "system": "http://hl7.org/fhir/sid/icd-10",
                "clinical_status": random.choice(["active", "resolved", "remission"]),
                "verification_status": "confirmed",
                "onset_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                "recorder_id": random.choice(practitioners).get("id") if practitioners else None
            }
            
            response = session.post(f"{BASE_URL}/conditions/", json=condition)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} conditions")

def create_observations(patients):
    """Create vital signs observations."""
    count = 0
    vital_types = [
        {"code": "8867-4", "display": "Heart rate", "unit": "beats/min", "min": 60, "max": 100},
        {"code": "8480-6", "display": "Systolic BP", "unit": "mmHg", "min": 110, "max": 140},
        {"code": "8462-4", "display": "Diastolic BP", "unit": "mmHg", "min": 70, "max": 90},
        {"code": "8310-5", "display": "Body temperature", "unit": "Cel", "min": 36, "max": 38},
        {"code": "9279-1", "display": "Respiratory rate", "unit": "breaths/min", "min": 12, "max": 20},
        {"code": "2708-6", "display": "SpO2", "unit": "%", "min": 94, "max": 100},
    ]
    
    for patient in patients:
        # Each patient gets vital signs for last 5 visits
        for days_ago in [0, 7, 14, 30, 60]:
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
            for vital in vital_types:
                obs = {
                    "patient_id": patient.get("id"),
                    "code": vital["code"],
                    "display": vital["display"],
                    "system": "http://loinc.org",
                    "value": round(random.uniform(vital["min"], vital["max"]), 1),
                    "unit": vital["unit"],
                    "effective_date": date,
                    "status": "final"
                }
                
                response = session.post(f"{BASE_URL}/observations/", json=obs)
                if response.status_code in [200, 201]:
                    count += 1
    print(f"✅ Created {count} vital signs observations")

def create_allergies(patients):
    """Create allergies for patients."""
    count = 0
    for patient in patients:
        # 30% of patients have allergies
        if random.random() < 0.3:
            num_allergies = random.randint(1, 2)
            selected = random.sample(ALLERGIES, num_allergies)
            for allergy in selected:
                allergy_data = {
                    "patient_id": patient.get("id"),
                    "substance": allergy,
                    "clinical_status": "active",
                    "verification_status": "confirmed",
                    "criticality": random.choice(["low", "high", "unable-to-assess"]),
                    "type": "allergy",
                    "category": ["medication"] if allergy in ["Penicilina", "Dipirona", "AAS", "Sulfa"] else ["food"]
                }
                
                response = session.post(f"{BASE_URL}/allergies/", json=allergy_data)
                if response.status_code in [200, 201]:
                    count += 1
    print(f"✅ Created {count} allergies")

def create_medications(patients, practitioners):
    """Create medication prescriptions."""
    count = 0
    for patient in patients:
        # Each patient gets 0-3 medications
        num_meds = random.randint(0, 3)
        selected = random.sample(MEDICATIONS, min(num_meds, len(MEDICATIONS)))
        for med in selected:
            medication = {
                "patient_id": patient.get("id"),
                "medication_name": med["name"],
                "rxcui": med["rxcui"],
                "status": random.choice(["active", "completed", "stopped"]),
                "dosage_instruction": f"Tomar 1 comprimido {random.choice(['1x ao dia', '2x ao dia', '3x ao dia'])}",
                "prescriber_id": random.choice(practitioners).get("id") if practitioners else None,
                "start_date": (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
            }
            
            response = session.post(f"{BASE_URL}/medications/", json=medication)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} medication prescriptions")

def create_appointments(patients, practitioners):
    """Create appointments."""
    count = 0
    for patient in patients:
        # Each patient gets 1-5 appointments
        num_appointments = random.randint(1, 5)
        for _ in range(num_appointments):
            # Past or future appointments
            days_offset = random.randint(-60, 30)
            start = datetime.now() + timedelta(days=days_offset, hours=random.randint(8, 17))
            
            appointment = {
                "patient_id": patient.get("id"),
                "practitioner_id": random.choice(practitioners).get("id") if practitioners else None,
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": random.choice(APPOINTMENT_STATUSES) if days_offset < 0 else "booked",
                "service_type": random.choice(SPECIALTIES),
                "description": f"Consulta de {random.choice(SPECIALTIES)}"
            }
            
            response = session.post(f"{BASE_URL}/appointments/", json=appointment)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} appointments")

def create_encounters(patients, practitioners, locations):
    """Create hospital encounters/admissions."""
    count = 0
    for patient in patients[:20]:  # 20 patients with admissions
        days_ago = random.randint(1, 30)
        start = datetime.now() - timedelta(days=days_ago)
        
        encounter = {
            "patient_id": patient.get("id"),
            "practitioner_id": random.choice(practitioners).get("id") if practitioners else None,
            "location_id": random.choice(locations).get("id") if locations else None,
            "status": random.choice(["in-progress", "finished"]),
            "class": "IMP",  # inpatient
            "type": "Internação hospitalar",
            "period_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "period_end": (start + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%dT%H:%M:%SZ") if random.random() > 0.3 else None,
            "reason": random.choice(ICD10_CODES)["display"]
        }
        
        response = session.post(f"{BASE_URL}/encounters/", json=encounter)
        if response.status_code in [200, 201]:
            count += 1
    print(f"✅ Created {count} encounters/admissions")

def create_visitors(patients):
    """Create visitors for patients."""
    count = 0
    for patient in patients[:20]:  # Visitors for admitted patients
        num_visitors = random.randint(1, 3)
        for _ in range(num_visitors):
            gender = random.choice(["male", "female"])
            first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
            last_name = random.choice(LAST_NAMES)
            
            visitor = {
                "patient_id": patient.get("id"),
                "name": f"{first_name} {last_name}",
                "relationship": random.choice(["Cônjuge", "Filho(a)", "Pai/Mãe", "Irmão(ã)", "Amigo(a)"]),
                "phone": generate_phone(),
                "document": generate_cpf(),
                "visit_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": random.choice(["checked-in", "checked-out"])
            }
            
            response = session.post(f"{BASE_URL}/visitors/", json=visitor)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} visitors")

def create_coverage(patients):
    """Create insurance coverage."""
    count = 0
    insurance_companies = ["Unimed", "Bradesco Saúde", "SulAmérica", "Amil", "Notre Dame", "Porto Seguro"]
    
    for patient in patients:
        if random.random() < 0.7:  # 70% have insurance
            coverage = {
                "patient_id": patient.get("id"),
                "payor": random.choice(insurance_companies),
                "subscriber_id": f"{random.randint(100000, 999999)}",
                "status": "active",
                "type": random.choice(["individual", "group"]),
                "period_start": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                "period_end": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            }
            
            response = session.post(f"{BASE_URL}/financial/coverage/", json=coverage)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} insurance coverages")

def create_invoices(patients):
    """Create financial invoices."""
    count = 0
    for patient in patients[:30]:  # 30 patients with invoices
        num_invoices = random.randint(1, 3)
        for _ in range(num_invoices):
            invoice = {
                "patient_id": patient.get("id"),
                "status": random.choice(["draft", "issued", "balanced", "cancelled"]),
                "date": (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
                "total": round(random.uniform(100, 5000), 2),
                "currency": "BRL",
                "items": [
                    {
                        "description": random.choice(["Consulta médica", "Exame de sangue", "Raio-X", "Ultrassonografia"]),
                        "amount": round(random.uniform(50, 500), 2)
                    }
                ]
            }
            
            response = session.post(f"{BASE_URL}/financial/invoices/", json=invoice)
            if response.status_code in [200, 201]:
                count += 1
    print(f"✅ Created {count} invoices")

def main():
    print("=" * 60)
    print("🏥 HealthStack - Comprehensive Data Seed")
    print("=" * 60)
    
    if not login():
        return
    
    print("\n📋 Creating data...")
    
    # Create in order of dependencies
    org_id = create_organization()
    practitioners = create_practitioners(20)
    locations = create_locations(30)
    patients = create_patients(50)
    
    if patients:
        create_conditions(patients, practitioners)
        create_observations(patients)
        create_allergies(patients)
        create_medications(patients, practitioners)
        create_appointments(patients, practitioners)
        create_encounters(patients, practitioners, locations)
        create_visitors(patients)
        create_coverage(patients)
        create_invoices(patients)
    
    print("\n" + "=" * 60)
    print("✅ Data seed complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
