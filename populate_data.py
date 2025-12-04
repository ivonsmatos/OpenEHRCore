import requests
import json
import datetime

# Configuração
API_URL = "http://localhost:8000/api/v1"
USERNAME = "medico@example.com"
PASSWORD = "senha123!@#"
PATIENT_ID = "patient-example-001"

def get_token():
    print("🔑 Autenticando...")
    response = requests.post(f"{API_URL}/auth/login/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Falha no login: {response.text}")
        exit(1)

def create_patient(token):
    # Tenta criar o paciente se não existir (embora o frontend use mock, o backend precisa dele para vincular dados)
    # Mas como o ID é 'patient-example-001', o backend pode não aceitar criar com ID específico via POST padrão
    # O FHIRService.create_patient_resource gera ID.
    # Vamos assumir que o usuário quer ver dados vinculados ao ID que o frontend mostra.
    # Se o backend validar a existência do paciente, precisaremos criar um.
    # Mas para popular dados, podemos tentar enviar o patient_id direto.
    pass

def populate_vital_signs(token):
    print("🩺 Criando Sinais Vitais...")
    headers = {"Authorization": f"Bearer {token}"}
    
    observations = [
        {
            "code": "8867-4", # Heart rate
            "value": 72,
            "unit": "bpm",
            "status": "final"
        },
        {
            "code": "8480-6", # Systolic blood pressure
            "value": 120,
            "unit": "mmHg",
            "status": "final"
        },
        {
            "code": "8462-4", # Diastolic blood pressure
            "value": 80,
            "unit": "mmHg",
            "status": "final"
        },
        {
            "code": "8310-5", # Body temperature
            "value": 36.5,
            "unit": "C",
            "status": "final"
        },
        {
            "code": "29463-7", # Body weight
            "value": 75.5,
            "unit": "kg",
            "status": "final"
        }
    ]

    for obs in observations:
        data = {
            "patient_id": PATIENT_ID,
            "code": obs["code"],
            "value": obs["value"],
            "status": obs["status"]
        }
        resp = requests.post(f"{API_URL}/observations/", json=data, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ {obs['code']}: {obs['value']} {obs['unit']}")
        else:
            print(f"  ❌ Falha {obs['code']}: {resp.text}")

def populate_conditions(token):
    print("⚠️ Criando Condições (Problemas)...")
    headers = {"Authorization": f"Bearer {token}"}
    
    conditions = [
        {
            "code": "38341003",
            "display": "Hipertensão Arterial",
            "clinical_status": "active",
            "verification_status": "confirmed"
        },
        {
            "code": "44054006",
            "display": "Diabetes Mellitus Tipo 2",
            "clinical_status": "active",
            "verification_status": "confirmed"
        }
    ]

    for cond in conditions:
        data = {
            "patient_id": PATIENT_ID,
            **cond
        }
        resp = requests.post(f"{API_URL}/conditions/", json=data, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ {cond['display']}")
        else:
            print(f"  ❌ Falha {cond['display']}: {resp.text}")

def populate_allergies(token):
    print("🤧 Criando Alergias...")
    headers = {"Authorization": f"Bearer {token}"}
    
    allergies = [
        {
            "code": "39579001",
            "display": "Alergia a Penicilina",
            "criticality": "high",
            "clinical_status": "active"
        },
        {
            "code": "91936005",
            "display": "Alergia a Poeira",
            "criticality": "low",
            "clinical_status": "active"
        }
    ]

    for alg in allergies:
        data = {
            "patient_id": PATIENT_ID,
            **alg
        }
        resp = requests.post(f"{API_URL}/allergies/", json=data, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ {alg['display']}")
        else:
            print(f"  ❌ Falha {alg['display']}: {resp.text}")

def populate_appointments(token):
    print("📅 Criando Agendamentos...")
    headers = {"Authorization": f"Bearer {token}"}
    
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    next_week = now + datetime.timedelta(days=7)

    appointments = [
        {
            "description": "Consulta de Rotina",
            "start": tomorrow.replace(hour=10, minute=0, second=0).isoformat(),
            "end": tomorrow.replace(hour=10, minute=30, second=0).isoformat(),
            "status": "booked"
        },
        {
            "description": "Retorno Cardiologista",
            "start": next_week.replace(hour=14, minute=0, second=0).isoformat(),
            "end": next_week.replace(hour=14, minute=30, second=0).isoformat(),
            "status": "booked"
        }
    ]

    for appt in appointments:
        data = {
            "patient_id": PATIENT_ID,
            **appt
        }
        resp = requests.post(f"{API_URL}/appointments/", json=data, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ {appt['description']}")
        else:
            print(f"  ❌ Falha {appt['description']}: {resp.text}")

if __name__ == "__main__":
    print("🚀 Iniciando população de dados...")
    token = get_token()
    
    # Primeiro, vamos garantir que o paciente exista no FHIR server com esse ID
    # O frontend usa um ID mockado, mas o backend vai tentar linkar dados a ele.
    # Se o FHIR server for estrito, pode reclamar se o Patient/{id} não existir.
    # Mas nossos métodos create_* apenas criam o recurso linkando o subject.
    # O HAPI FHIR geralmente aceita referências a recursos inexistentes se não tiver validação referencial estrita ativada.
    # Se falhar, teremos que criar o paciente primeiro com PUT.
    
    populate_vital_signs(token)
    populate_conditions(token)
    populate_allergies(token)
    populate_appointments(token)
    
    print("\n✨ Concluído! Atualize o painel do paciente.")
