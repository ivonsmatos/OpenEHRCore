"""
Seed clínico mais rico: adiciona pacientes com condições (coerentes por idade),
medicações, alergias, vacinas, sinais vitais e encontros — para um demo populado.

Run: FHIR_SERVER_URL=http://hapi-fhir:8080/fhir python scripts/seed_clinical_rich.py
"""

import os
import random
from datetime import datetime, timedelta

import requests

FHIR = os.environ.get("FHIR_SERVER_URL", "http://localhost:8080/fhir")
H = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

GIVEN = ["Maria", "José", "Ana", "João", "Francisca", "Carlos", "Antônia", "Paulo",
         "Adriana", "Marcos", "Juliana", "Pedro", "Fernanda", "Lucas", "Patrícia",
         "Rafael", "Camila", "Bruno", "Beatriz", "Gustavo"]
FAMILY = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa",
          "Almeida", "Nascimento", "Araújo", "Ribeiro", "Carvalho", "Gomes", "Rocha"]

COND_BY_AGE = {
    "child": [("195967001", "Asma"), ("3110003", "Otite média aguda"), ("24079001", "Dermatite atópica")],
    "young": [("195967001", "Asma"), ("48694002", "Transtorno de ansiedade"), ("37796009", "Enxaqueca"), ("13644009", "Hipotireoidismo")],
    "adult": [("38341003", "Hipertensão arterial"), ("73211009", "Diabetes mellitus tipo 2"), ("13644009", "Hipotireoidismo"), ("48694002", "Transtorno de ansiedade")],
    "elderly": [("38341003", "Hipertensão arterial"), ("73211009", "Diabetes mellitus tipo 2"), ("56265001", "Insuficiência cardíaca"), ("13645005", "DPOC"), ("49436004", "Fibrilação atrial")],
}
MEDS = ["Losartana 50 mg", "Metformina 850 mg", "Sinvastatina 20 mg", "Omeprazol 20 mg",
        "Levotiroxina 50 mcg", "AAS 100 mg", "Salbutamol aerossol"]
ALLERGIES = [("373270004", "Penicilina"), ("227493005", "Frutos do mar"), ("412071004", "Dipirona"), ("91935009", "Amendoim")]
VACCINES = ["BCG", "Febre amarela", "Influenza", "Dupla adulto (dT)", "COVID-19", "Hepatite B"]


def create(rt, res):
    try:
        r = requests.post(f"{FHIR}/{rt}", headers=H, json=res, timeout=20)
        return r.status_code in (200, 201)
    except requests.RequestException:
        return False


def _ago(days_max, days_min=0):
    return (datetime.utcnow() - timedelta(days=random.randint(days_min, days_max))).isoformat()


def age_group(age):
    return "child" if age < 13 else "young" if age < 40 else "adult" if age < 65 else "elderly"


def main():
    c = {k: 0 for k in ("pt", "cond", "med", "allergy", "vital", "enc", "imm")}
    prs = [e["resource"]["id"] for e in
           requests.get(f"{FHIR}/Practitioner?_count=20", headers=H, timeout=20).json().get("entry", [])]

    for _ in range(15):
        age = random.randint(2, 88)
        birth = (datetime.utcnow() - timedelta(days=age * 365)).strftime("%Y-%m-%d")
        given, family = random.choice(GIVEN), random.choice(FAMILY)
        ok = create("Patient", {
            "resourceType": "Patient", "active": True,
            "name": [{"use": "official", "text": f"{given} {family}", "given": [given], "family": family}],
            "gender": random.choice(["male", "female"]), "birthDate": birth,
            "telecom": [{"system": "phone", "value": f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"}],
        })
        if not ok:
            continue
        # pega o id do paciente recém-criado pelo nome (simplificado: busca o último)
        found = requests.get(f"{FHIR}/Patient?family={family}&given={given}&_sort=-_lastUpdated&_count=1",
                             headers=H, timeout=20).json().get("entry", [])
        if not found:
            continue
        pid = found[0]["resource"]["id"]
        c["pt"] += 1
        grp = age_group(age)

        for code, disp in random.sample(COND_BY_AGE[grp], random.randint(1, min(3, len(COND_BY_AGE[grp])))):
            if create("Condition", {
                "resourceType": "Condition",
                "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
                "code": {"coding": [{"system": "http://snomed.info/sct", "code": code, "display": disp}], "text": disp},
                "subject": {"reference": f"Patient/{pid}"}, "onsetDateTime": _ago(1500, 30),
            }):
                c["cond"] += 1

        for disp in random.sample(MEDS, random.randint(1, 4)):
            if create("MedicationRequest", {
                "resourceType": "MedicationRequest", "status": "active", "intent": "order",
                "medicationCodeableConcept": {"text": disp}, "subject": {"reference": f"Patient/{pid}"},
                "authoredOn": _ago(200, 1), "dosageInstruction": [{"text": "1 vez ao dia"}],
            }):
                c["med"] += 1

        for code, disp in random.sample(ALLERGIES, random.randint(0, 2)):
            if create("AllergyIntolerance", {
                "resourceType": "AllergyIntolerance",
                "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
                "code": {"coding": [{"system": "http://snomed.info/sct", "code": code, "display": disp}], "text": disp},
                "patient": {"reference": f"Patient/{pid}"},
            }):
                c["allergy"] += 1

        for _ in range(random.randint(2, 4)):
            if create("Observation", {
                "resourceType": "Observation", "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Pressão arterial"}], "text": "Pressão arterial"},
                "subject": {"reference": f"Patient/{pid}"}, "effectiveDateTime": _ago(120),
                "component": [
                    {"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]}, "valueQuantity": {"value": random.randint(105, 150), "unit": "mmHg"}},
                    {"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4"}]}, "valueQuantity": {"value": random.randint(65, 95), "unit": "mmHg"}},
                ],
            }):
                c["vital"] += 1

        for _ in range(random.randint(1, 3)):
            enc = {
                "resourceType": "Encounter", "status": random.choice(["finished", "in-progress"]),
                "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatorial"},
                "subject": {"reference": f"Patient/{pid}"}, "period": {"start": _ago(90)},
            }
            if prs:
                enc["participant"] = [{"individual": {"reference": f"Practitioner/{random.choice(prs)}"}}]
            if create("Encounter", enc):
                c["enc"] += 1

        for disp in random.sample(VACCINES, random.randint(1, 3)):
            if create("Immunization", {
                "resourceType": "Immunization", "status": "completed",
                "vaccineCode": {"text": disp}, "patient": {"reference": f"Patient/{pid}"},
                "occurrenceDateTime": _ago(2000, 30),
            }):
                c["imm"] += 1

    print("Seed clínico rico:", c)


if __name__ == "__main__":
    main()
