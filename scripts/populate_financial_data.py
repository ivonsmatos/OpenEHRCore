import os
import sys
import django
from datetime import datetime, timedelta
import json

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend-django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api.services.fhir_core import FHIRService

def populate_financial():
    service = FHIRService()
    patient_id = "patient-1"

    print(f"Populating Financial data for {patient_id}...")

    # 1. Create Coverage (Unimed)
    try:
        print("Creating Coverage (Unimed)...")
        cov = service.create_coverage_resource(
            patient_id=patient_id,
            payor_name="Unimed São Paulo",
            subscriber_id="123456789",
            status="active",
            type_text="Plano de Saúde Individual"
        )
        print(f"Coverage created: {cov.get('id')}")
    except Exception as e:
        print(f"Failed to create Coverage: {e}")

    # 2. Create Patient Account
    account_id = None
    try:
        print("Creating Account...")
        acc = service.create_account_resource(
            patient_id=patient_id,
            name="Conta Principal - Paciente Teste"
        )
        account_id = acc.get('id')
        print(f"Account created: {account_id}")
    except Exception as e:
        print(f"Failed to create Account: {e}")

    # 3. Create Invoices
    try:
        if account_id:
            print("Creating Invoices...")
            # Invoice 1 - Pago (Simulação de status na criação não suportado 100% pelo meu método simples, mas vamos tentar 'balanced')
            # O metodo aceita 'status', então:
            inv1 = service.create_invoice_resource(
                patient_id=patient_id,
                account_id=account_id,
                total_gross=450.00,
                status="issued" # Emitido (pendente)
            )
            print(f"Invoice 1 created: {inv1.get('id')} - R$ 450.00")

            inv2 = service.create_invoice_resource(
                patient_id=patient_id,
                account_id=account_id,
                total_gross=150.00,
                status="balanced" # Pago/Fechado
            )
            print(f"Invoice 2 created: {inv2.get('id')} - R$ 150.00")
            
    except Exception as e:
        print(f"Failed to create Invoices: {e}")

    print("\nFinancial Data Population Complete!")

if __name__ == "__main__":
    populate_financial()
