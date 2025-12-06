import requests
import random
from datetime import datetime, timedelta
import json

FHIR_URL = "http://localhost:8080/fhir"

def create_patient(first, last, gender, birth_date):
    patient = {
        "resourceType": "Patient",
        "name": [{"family": last, "given": [first]}],
        "gender": gender,
        "birthDate": birth_date
    }
    r = requests.post(f"{FHIR_URL}/Patient", json=patient)
    if r.status_code == 201:
        return r.json()["id"]
    return None

def create_encounter(patient_id, practitioner_name, reason):
    date = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
    encounter = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter"
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "participant": [
            {
                "individual": {"display": practitioner_name}
            }
        ],
        "period": {"start": date},
        "reasonCode": [
            {
                "text": reason
            }
        ]
    }
    requests.post(f"{FHIR_URL}/Encounter", json=encounter)

# Data to seed
patients_data = [
    ("Ana", "Silva", "female", "1985-04-12"),
    ("Carlos", "Oliveira", "male", "1990-08-23"),
    ("Maria", "Santos", "female", "1978-11-30"),
    ("Joao", "Pereira", "male", "1965-02-15"),
    ("Lucia", "Ferreira", "female", "1992-06-10")
]

reasons = ["Check-up", "Febre Alta", "Dor Abdominal", "Influenza", "Hipertensão"]
doctors = ["Dr. House", "Dr. Wilson", "Dra. Cameron", "Dr. Chase"]

print("Populando servidor FHIR...")
count = 0
for p in patients_data:
    pid = create_patient(*p)
    if pid:
        # Create 1-3 encounters for each patient
        for _ in range(random.randint(1, 3)):
            create_encounter(pid, random.choice(doctors), random.choice(reasons))
            count += 1

print(f"Sucesso! {len(patients_data)} pacientes e {count} admissões criadas.")
