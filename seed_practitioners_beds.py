"""
Populate Practitioners and Beds via Django API
Uses correct format expected by Django endpoints
"""

import requests
import random
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
FHIR_URL = "http://localhost:8080/fhir"
USERNAME = "contato@ivonmatos.com.br"
PASSWORD = "Protonsysdba@1986"

FIRST_NAMES_M = ["João", "Pedro", "Lucas", "Matheus", "Gabriel", "Rafael", "Bruno", "Carlos", "André", "Felipe"]
FIRST_NAMES_F = ["Maria", "Ana", "Julia", "Beatriz", "Larissa", "Camila", "Fernanda", "Amanda", "Carolina", "Patricia"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes"]
SPECIALTIES = [
    ("394579002", "Cardiologia"),
    ("394585009", "Gastroenterologia"),
    ("394587001", "Psiquiatria"),
    ("394591006", "Neurologia"),
    ("394610002", "Cirurgia Geral"),
    ("394611003", "Pediatria"),
    ("408443003", "Medicina de Emergência"),
    ("394598000", "Oftalmologia"),
]

session = requests.Session()
token = None

def login():
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

def create_practitioners():
    """Create 20 practitioners via Django API"""
    print("\n📋 Creating practitioners...")
    count = 0
    
    for i in range(20):
        gender = random.choice(["male", "female"])
        first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        specialty = random.choice(SPECIALTIES)
        
        practitioner = {
            "family_name": last_name,
            "given_names": [first_name],
            "prefix": "Dr." if i < 15 else "Enf.",
            "gender": gender,
            "birthDate": f"{random.randint(1960, 1990)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "phone": f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@hospital.com",
            "crm": f"CRM-SP-{random.randint(100000, 999999)}",
            "qualification_code": "MD" if i < 15 else "RN",
            "qualification_display": specialty[1] if i < 15 else "Enfermeiro(a)"
        }
        
        response = session.post(f"{BASE_URL}/practitioners/", json=practitioner)
        if response.status_code in [200, 201]:
            count += 1
            print(f"  ✅ {practitioner['prefix']} {first_name} {last_name}")
        else:
            print(f"  ⚠️ Error: {response.status_code} - {response.text[:100]}")
        time.sleep(0.2)
    
    print(f"  Created {count}/20 practitioners")
    return count

def create_locations_direct():
    """Create hospital structure with beds directly in HAPI FHIR"""
    print("\n📋 Creating hospital structure and beds...")
    
    fhir_session = requests.Session()
    fhir_session.headers.update({
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    })
    
    # Create Hospital
    hospital = {
        "resourceType": "Location",
        "status": "active",
        "name": "Hospital OpenEHRCore",
        "description": "Hospital geral com todas especialidades",
        "mode": "instance",
        "type": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "HOSP",
                "display": "Hospital"
            }]
        }],
        "physicalType": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "bu",
                "display": "Building"
            }]
        }
    }
    
    resp = fhir_session.post(f"{FHIR_URL}/Location", json=hospital)
    if resp.status_code != 201:
        print(f"  ⚠️ Hospital creation failed: {resp.status_code}")
        return 0
    
    hospital_id = resp.json()["id"]
    print(f"  ✅ Hospital created: {hospital_id}")
    
    # Create Departments (Wings)
    departments = ["UTI", "Enfermaria Geral", "Centro Cirúrgico", "Pronto Socorro", "Pediatria", "Maternidade"]
    dept_ids = {}
    
    for dept_name in departments:
        dept = {
            "resourceType": "Location",
            "status": "active",
            "name": dept_name,
            "mode": "instance",
            "type": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "HU",
                    "display": "Hospital unit"
                }]
            }],
            "physicalType": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                    "code": "wi",
                    "display": "Wing"
                }]
            },
            "partOf": {"reference": f"Location/{hospital_id}"}
        }
        
        resp = fhir_session.post(f"{FHIR_URL}/Location", json=dept)
        if resp.status_code == 201:
            dept_ids[dept_name] = resp.json()["id"]
            print(f"  ✅ Department: {dept_name}")
    
    # Create Beds for each department
    bed_count = 0
    statuses = [
        ("U", "Unoccupied", 5),    # 5 free beds per dept
        ("O", "Occupied", 3),      # 3 occupied beds per dept
        ("K", "Contaminated", 1),  # 1 cleaning bed per dept
        ("I", "Temporarily Closed", 1)  # 1 blocked bed per dept
    ]
    
    for dept_name, dept_id in dept_ids.items():
        bed_num = 1
        for status_code, status_display, count in statuses:
            for _ in range(count):
                bed = {
                    "resourceType": "Location",
                    "status": "active" if status_code != "I" else "inactive",
                    "name": f"Leito {dept_name[:3].upper()}-{bed_num:02d}",
                    "description": f"Leito {bed_num} - {dept_name}",
                    "mode": "instance",
                    "type": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                            "code": "PTRES",
                            "display": "Patient Room"
                        }]
                    }],
                    "physicalType": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                            "code": "bd",
                            "display": "Bed"
                        }]
                    },
                    "partOf": {"reference": f"Location/{dept_id}"},
                    "operationalStatus": {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                        "code": status_code,
                        "display": status_display
                    }
                }
                
                resp = fhir_session.post(f"{FHIR_URL}/Location", json=bed)
                if resp.status_code == 201:
                    bed_count += 1
                bed_num += 1
        time.sleep(0.1)
    
    print(f"  ✅ Created {bed_count} beds across {len(dept_ids)} departments")
    return bed_count

def main():
    print("=" * 60)
    print("🏥 OpenEHRCore - Practitioners & Beds Seed")
    print("=" * 60)
    
    if not login():
        return
    
    create_practitioners()
    create_locations_direct()
    
    print("\n" + "=" * 60)
    print("✅ Seed complete!")
    print("   Refresh the frontend to see the data")
    print("=" * 60)

if __name__ == "__main__":
    main()
