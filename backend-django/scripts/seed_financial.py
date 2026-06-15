"""
Semeia dados financeiros (Coverage + Invoice) para popular o Financial Dashboard.
Lê FHIR_SERVER_URL do ambiente. Idempotência simples: pula se já houver Invoices.

Run: FHIR_SERVER_URL=http://hapi-fhir:8080/fhir python scripts/seed_financial.py
"""

import os
import random
from datetime import datetime, timedelta

import requests

FHIR_URL = os.environ.get("FHIR_SERVER_URL", "http://localhost:8080/fhir")
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
PAYERS = ["Unimed", "Bradesco Saúde", "SulAmérica", "Amil", "Porto Seguro", "Particular"]


def _create(resource_type, resource):
    try:
        r = requests.post(f"{FHIR_URL}/{resource_type}", headers=HEADERS, json=resource, timeout=20)
        return r.status_code in (200, 201)
    except requests.RequestException:
        return False


def main():
    existing = requests.get(f"{FHIR_URL}/Invoice?_summary=count", headers=HEADERS, timeout=20).json()
    if existing.get("total", 0) > 0:
        print(f"Já existem {existing['total']} Invoices — nada a semear.")
        return

    pts = requests.get(f"{FHIR_URL}/Patient?_count=50", headers=HEADERS, timeout=20).json().get("entry", [])
    pids = [e["resource"]["id"] for e in pts]
    if not pids:
        print("Sem pacientes para vincular finanças.")
        return

    cov = inv = 0
    for pid in pids:
        payer = random.choice(PAYERS)
        if payer != "Particular":
            if _create("Coverage", {
                "resourceType": "Coverage", "status": "active",
                "beneficiary": {"reference": f"Patient/{pid}"},
                "payor": [{"display": payer}],
            }):
                cov += 1
        for _ in range(random.randint(2, 5)):
            date = (datetime.utcnow() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
            status = random.choices(["balanced", "issued"], weights=[7, 3])[0]
            if _create("Invoice", {
                "resourceType": "Invoice", "status": status,
                "subject": {"reference": f"Patient/{pid}"},
                "recipient": {"display": payer},
                "date": date,
                "totalGross": {"value": round(random.uniform(80, 2500), 2), "currency": "BRL"},
            }):
                inv += 1
    print(f"Semeado: {cov} Coverage, {inv} Invoice.")


if __name__ == "__main__":
    main()
