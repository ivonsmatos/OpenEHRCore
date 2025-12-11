"""
Script para popular dados clínicos de exemplo para TODOS os pacientes no HAPI FHIR

Cria dados de exemplo para cada paciente encontrado:
- Sinais Vitais (Observations)
- Vacinas (Immunizations)
- Resultado de Exames (DiagnosticReports)
- Medicamentos (MedicationRequests)
- Histórico Clínico (Conditions)
- Alergias (AllergyIntolerance)
- Agendamentos (Appointments)
- Atendimentos (Encounters)

Uso:
    python populate_clinical_data.py [--max N] [--patient-id ID]
    
    --max N       : Limita a N pacientes (default: todos)
    --patient-id  : Popula apenas para um paciente específico
"""

import requests
import json
from datetime import datetime, timedelta
import random
import sys

HAPI_FHIR_URL = "http://localhost:8080/fhir"


def get_all_patients(max_count=100):
    """Busca todos os pacientes do HAPI FHIR"""
    patients = []
    response = requests.get(f"{HAPI_FHIR_URL}/Patient?_count={max_count}")
    if response.status_code == 200:
        bundle = response.json()
        if bundle.get("entry"):
            for entry in bundle["entry"]:
                patients.append(entry["resource"])
    return patients


def get_patient_name(patient):
    """Extrai nome do paciente"""
    name = patient.get('name', [{}])[0]
    given = name.get('given', [''])[0] if name.get('given') else ''
    family = name.get('family', '')
    return f"{given} {family}".strip() or f"Paciente {patient['id']}"


def create_vital_signs(patient_id: str):
    """Cria sinais vitais de exemplo para os últimos 30 dias"""
    observations = []
    
    for days_ago in range(30, 0, -5):  # A cada 5 dias
        date = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # Pressão Arterial
        bp = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": date,
            "component": [
                {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]}, "valueQuantity": {"value": random.randint(110, 145), "unit": "mmHg"}},
                {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4"}]}, "valueQuantity": {"value": random.randint(65, 95), "unit": "mmHg"}}
            ]
        }
        observations.append(bp)
        
        # Frequência Cardíaca
        observations.append({
            "resourceType": "Observation", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": date,
            "valueQuantity": {"value": random.randint(58, 105), "unit": "beats/min"}
        })
        
        # Temperatura
        observations.append({
            "resourceType": "Observation", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": date,
            "valueQuantity": {"value": round(random.uniform(35.8, 37.8), 1), "unit": "°C"}
        })
        
        # SpO2
        observations.append({
            "resourceType": "Observation", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "59408-5", "display": "SpO2"}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": date,
            "valueQuantity": {"value": random.randint(94, 100), "unit": "%"}
        })
    
    created = 0
    for obs in observations:
        if requests.post(f"{HAPI_FHIR_URL}/Observation", json=obs).status_code == 201:
            created += 1
    return created


def create_immunizations(patient_id: str):
    """Cria vacinas de exemplo"""
    vaccines = [
        {"code": "08", "display": "Hepatite B", "days": -random.randint(100, 400)},
        {"code": "03", "display": "MMR", "days": -random.randint(50, 200)},
        {"code": "115", "display": "COVID-19", "days": -random.randint(30, 120)},
        {"code": "140", "display": "Influenza 2024", "days": -random.randint(10, 60)},
    ]
    
    created = 0
    for v in vaccines:
        imm = {
            "resourceType": "Immunization", "status": "completed",
            "vaccineCode": {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": v["code"], "display": v["display"]}]},
            "patient": {"reference": f"Patient/{patient_id}"},
            "occurrenceDateTime": (datetime.now() + timedelta(days=v["days"])).strftime("%Y-%m-%d"),
            "primarySource": True
        }
        if requests.post(f"{HAPI_FHIR_URL}/Immunization", json=imm).status_code == 201:
            created += 1
    return created


def create_diagnostic_reports(patient_id: str):
    """Cria resultados de exames"""
    exams = [
        {"code": "58410-2", "display": "Hemograma", "conclusion": "Valores normais"},
        {"code": "2345-7", "display": "Glicemia", "conclusion": f"Glicemia: {random.randint(80, 120)} mg/dL"},
        {"code": "2093-3", "display": "Colesterol Total", "conclusion": f"Colesterol: {random.randint(150, 220)} mg/dL"},
    ]
    
    created = 0
    for e in exams:
        report = {
            "resourceType": "DiagnosticReport", "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": e["code"], "display": e["display"]}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": (datetime.now() - timedelta(days=random.randint(5, 30))).isoformat(),
            "conclusion": e["conclusion"]
        }
        if requests.post(f"{HAPI_FHIR_URL}/DiagnosticReport", json=report).status_code == 201:
            created += 1
    return created


def create_medications(patient_id: str):
    """Cria prescrições de medicamentos"""
    meds = [
        {"name": "Losartana 50mg", "status": "active"},
        {"name": "Metformina 850mg", "status": "active"},
        {"name": "Omeprazol 20mg", "status": random.choice(["active", "completed"])},
    ]
    
    created = 0
    for m in meds:
        med = {
            "resourceType": "MedicationRequest", "status": m["status"], "intent": "order",
            "medicationCodeableConcept": {"text": m["name"]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "authoredOn": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            "requester": {"display": "Dr. Carlos Mendes"}
        }
        if requests.post(f"{HAPI_FHIR_URL}/MedicationRequest", json=med).status_code == 201:
            created += 1
    return created


def create_conditions(patient_id: str):
    """Cria condições/problemas de saúde"""
    conditions = [
        {"code": "38341003", "display": "Hipertensão", "status": "active"},
        {"code": "44054006", "display": "Diabetes tipo 2", "status": random.choice(["active", "inactive"])},
    ]
    
    created = 0
    for c in conditions:
        cond = {
            "resourceType": "Condition",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": c["status"]}]},
            "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": c["code"], "display": c["display"]}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": (datetime.now() - timedelta(days=random.randint(100, 1000))).strftime("%Y-%m-%d")
        }
        if requests.post(f"{HAPI_FHIR_URL}/Condition", json=cond).status_code == 201:
            created += 1
    return created


def create_allergies(patient_id: str):
    """Cria alergias"""
    allergies = [{"display": "Penicilina", "severity": "severe"}, {"display": "Dipirona", "severity": "moderate"}]
    
    created = 0
    for a in allergies:
        allergy = {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
            "code": {"text": a["display"]},
            "patient": {"reference": f"Patient/{patient_id}"},
            "reaction": [{"severity": a["severity"]}]
        }
        if requests.post(f"{HAPI_FHIR_URL}/AllergyIntolerance", json=allergy).status_code == 201:
            created += 1
    return created


def create_appointments(patient_id: str):
    """Cria agendamentos"""
    created = 0
    for days in [7, 14, -7]:
        start = datetime.now().replace(hour=random.randint(8, 16), minute=0) + timedelta(days=days)
        apt = {
            "resourceType": "Appointment",
            "status": "booked" if days > 0 else "fulfilled",
            "start": start.isoformat(), "end": (start + timedelta(minutes=30)).isoformat(),
            "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}]
        }
        if requests.post(f"{HAPI_FHIR_URL}/Appointment", json=apt).status_code == 201:
            created += 1
    return created


def create_encounters(patient_id: str):
    """Cria atendimentos históricos"""
    created = 0
    for days_ago in [30, 90]:
        enc = {
            "resourceType": "Encounter", "status": "finished",
            "class": {"code": "AMB"},
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {"start": (datetime.now() - timedelta(days=days_ago)).isoformat()}
        }
        if requests.post(f"{HAPI_FHIR_URL}/Encounter", json=enc).status_code == 201:
            created += 1
    return created


def populate_patient(patient_id: str, patient_name: str, index: int):
    """Popula todos os dados clínicos para um paciente"""
    print(f"\n[{index}] 👤 {patient_name} (ID: {patient_id})")
    
    totals = {
        "vitals": create_vital_signs(patient_id),
        "vaccines": create_immunizations(patient_id),
        "exams": create_diagnostic_reports(patient_id),
        "meds": create_medications(patient_id),
        "conditions": create_conditions(patient_id),
        "allergies": create_allergies(patient_id),
        "appointments": create_appointments(patient_id),
        "encounters": create_encounters(patient_id)
    }
    
    total = sum(totals.values())
    print(f"    ✓ {total} recursos ({totals['vitals']} vitais, {totals['vaccines']} vacinas, {totals['exams']} exames, {totals['meds']} meds, {totals['conditions']} cond, {totals['allergies']} alerg, {totals['appointments']} agend, {totals['encounters']} atend)")
    return total


def main():
    print("=" * 70)
    print("🏥 OpenEHRCore - Populando Dados Clínicos para TODOS os Pacientes")
    print("=" * 70)
    
    # Parse argumentos
    max_patients = None
    specific_patient = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--max" and i < len(sys.argv) - 1:
            max_patients = int(sys.argv[i + 1])
        elif arg == "--patient-id" and i < len(sys.argv) - 1:
            specific_patient = sys.argv[i + 1]
    
    if specific_patient:
        # Popular apenas um paciente específico
        response = requests.get(f"{HAPI_FHIR_URL}/Patient/{specific_patient}")
        if response.status_code == 200:
            patient = response.json()
            populate_patient(specific_patient, get_patient_name(patient), 1)
        else:
            print(f"❌ Paciente {specific_patient} não encontrado!")
        return
    
    # Buscar todos os pacientes
    patients = get_all_patients(max_patients or 100)
    
    if not patients:
        print("\n❌ Nenhum paciente encontrado no HAPI FHIR!")
        return
    
    print(f"\n📋 Encontrados {len(patients)} pacientes")
    
    grand_total = 0
    for idx, patient in enumerate(patients, 1):
        total = populate_patient(patient["id"], get_patient_name(patient), idx)
        grand_total += total
    
    print("\n" + "=" * 70)
    print(f"✅ CONCLUÍDO! {grand_total} recursos FHIR criados para {len(patients)} pacientes")
    print("=" * 70)
    print(f"\n🔗 Acesse: http://localhost:3000/patients")


if __name__ == "__main__":
    main()
