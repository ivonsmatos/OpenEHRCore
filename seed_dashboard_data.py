"""
Seed Dashboard Data - Encounters, Procedures, and Appointments for today
"""

import requests
import random
from datetime import datetime, timedelta

FHIR_URL = "http://localhost:8080/fhir"

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/fhir+json',
    'Accept': 'application/fhir+json'
})

def get_patients():
    """Get existing patients"""
    resp = session.get(f"{FHIR_URL}/Patient", params={"_count": 50})
    if resp.status_code == 200:
        bundle = resp.json()
        return [e["resource"] for e in bundle.get("entry", [])]
    return []

def get_practitioners():
    """Get existing practitioners"""
    resp = session.get(f"{FHIR_URL}/Practitioner", params={"_count": 20})
    if resp.status_code == 200:
        bundle = resp.json()
        return [e["resource"] for e in bundle.get("entry", [])]
    return []

def get_patient_name(patient):
    """Extract patient display name"""
    if patient.get("name"):
        name = patient["name"][0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        return f"{given} {family}".strip()
    return f"Patient/{patient['id']}"

def get_practitioner_name(practitioner):
    """Extract practitioner display name"""
    if practitioner.get("name"):
        name = practitioner["name"][0]
        prefix = " ".join(name.get("prefix", []))
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        return f"{prefix} {given} {family}".strip()
    return f"Practitioner/{practitioner['id']}"

def create_encounters(patients, practitioners):
    """Create Encounter resources (IPD admissions)"""
    print("\n📋 Creating Encounters (Admissions)...")
    count = 0
    today = datetime.now()
    
    reasons = [
        ("J18.9", "Pneumonia"),
        ("I10", "Hipertensão Essencial"),
        ("K35.9", "Apendicite Aguda"),
        ("S72.0", "Fratura de Fêmur"),
        ("E11.9", "Diabetes Mellitus Tipo 2"),
        ("N39.0", "Infecção Urinária"),
        ("J44.1", "Doença Pulmonar Obstrutiva Crônica"),
        ("I21.9", "Infarto Agudo do Miocárdio")
    ]
    
    # Create 15 inpatient encounters (admissions)
    for i in range(15):
        patient = random.choice(patients)
        practitioner = random.choice(practitioners)
        reason = random.choice(reasons)
        
        # Random admission within last 5 days
        days_ago = random.randint(0, 5)
        admission_date = today - timedelta(days=days_ago)
        
        encounter = {
            "resourceType": "Encounter",
            "status": random.choice(["in-progress", "finished"]),
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter"
            },
            "type": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "32485007",
                    "display": "Hospital admission"
                }]
            }],
            "subject": {
                "reference": f"Patient/{patient['id']}",
                "display": get_patient_name(patient)
            },
            "participant": [{
                "type": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "ATND",
                        "display": "attender"
                    }]
                }],
                "individual": {
                    "reference": f"Practitioner/{practitioner['id']}",
                    "display": get_practitioner_name(practitioner)
                }
            }],
            "period": {
                "start": admission_date.strftime("%Y-%m-%dT%H:%M:%S-03:00")
            },
            "reasonCode": [{
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": reason[0],
                    "display": reason[1]
                }],
                "text": reason[1]
            }],
            "location": [{
                "location": {
                    "display": f"Quarto {100 + i}"
                },
                "status": "active"
            }]
        }
        
        resp = session.post(f"{FHIR_URL}/Encounter", json=encounter)
        if resp.status_code == 201:
            count += 1
            
    print(f"  ✅ Created {count} admissions")
    return count

def create_procedures(patients, practitioners):
    """Create Procedure resources (surgeries)"""
    print("\n📋 Creating Procedures (Surgeries)...")
    count = 0
    today = datetime.now()
    
    surgeries = [
        ("80146002", "Apendicectomia"),
        ("36969009", "Colecistectomia"),
        ("90470006", "Cesariana"),
        ("287664005", "Cirurgia de Catarata"),
        ("40701008", "Artroscopia de Joelho"),
        ("234319005", "Herniorrafia Inguinal"),
        ("397956004", "Rinoplastia"),
        ("18557009", "Bypass Coronário")
    ]
    
    # Create 8 procedures for today
    for i in range(8):
        patient = random.choice(patients)
        practitioner = random.choice(practitioners)
        surgery = random.choice(surgeries)
        
        # Surgeries scheduled for today
        surgery_time = today.replace(hour=7 + i, minute=0, second=0)
        
        procedure = {
            "resourceType": "Procedure",
            "status": random.choice(["in-progress", "completed"]),
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": surgery[0],
                    "display": surgery[1]
                }],
                "text": surgery[1]
            },
            "subject": {
                "reference": f"Patient/{patient['id']}",
                "display": get_patient_name(patient)
            },
            "performedDateTime": surgery_time.strftime("%Y-%m-%dT%H:%M:%S-03:00"),
            "performer": [{
                "actor": {
                    "reference": f"Practitioner/{practitioner['id']}",
                    "display": get_practitioner_name(practitioner)
                }
            }]
        }
        
        resp = session.post(f"{FHIR_URL}/Procedure", json=procedure)
        if resp.status_code == 201:
            count += 1
            
    print(f"  ✅ Created {count} surgeries for today")
    return count

def create_ambulatory_appointments(patients, practitioners):
    """Create Appointments for today (ambulatory)"""
    print("\n📋 Creating Today's Ambulatory Appointments...")
    count = 0
    today = datetime.now()
    
    services = [
        "Consulta de Rotina",
        "Retorno Cardiologia",
        "Exame de Sangue",
        "Avaliação Pré-Operatória",
        "Fisioterapia",
        "Consulta Dermatologia",
        "Retorno Ortopedia",
        "Avaliação Nutricional"
    ]
    
    # Create 25 appointments for today
    for i in range(25):
        patient = random.choice(patients)
        practitioner = random.choice(practitioners)
        service = random.choice(services)
        
        # Appointments throughout today
        appt_time = today.replace(hour=8 + (i % 10), minute=(i * 15) % 60, second=0)
        end_time = appt_time + timedelta(minutes=30)
        
        appointment = {
            "resourceType": "Appointment",
            "status": random.choice(["booked", "arrived", "fulfilled"]),
            "serviceType": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/service-type",
                    "code": "124",
                    "display": service
                }],
                "text": service
            }],
            "start": appt_time.strftime("%Y-%m-%dT%H:%M:%S-03:00"),
            "end": end_time.strftime("%Y-%m-%dT%H:%M:%S-03:00"),
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{patient['id']}",
                        "display": get_patient_name(patient)
                    },
                    "status": "accepted"
                },
                {
                    "actor": {
                        "reference": f"Practitioner/{practitioner['id']}",
                        "display": get_practitioner_name(practitioner)
                    },
                    "status": "accepted"
                }
            ]
        }
        
        resp = session.post(f"{FHIR_URL}/Appointment", json=appointment)
        if resp.status_code == 201:
            count += 1
            
    print(f"  ✅ Created {count} ambulatory appointments for today")
    return count

def main():
    print("=" * 60)
    print("🏥 OpenEHRCore - Dashboard Data Seed")
    print("=" * 60)
    
    patients = get_patients()
    practitioners = get_practitioners()
    
    if not patients:
        print("❌ No patients found! Run seed_fhir_direct.py first")
        return
    if not practitioners:
        print("❌ No practitioners found! Run seed_practitioners_beds.py first")
        return
    
    print(f"Found {len(patients)} patients and {len(practitioners)} practitioners")
    
    create_encounters(patients, practitioners)
    create_procedures(patients, practitioners)
    create_ambulatory_appointments(patients, practitioners)
    
    print("\n" + "=" * 60)
    print("✅ Dashboard data seed complete!")
    print("   Refresh the Dashboard to see the populated KPIs")
    print("=" * 60)

if __name__ == "__main__":
    main()
