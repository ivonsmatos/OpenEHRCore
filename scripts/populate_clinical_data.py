"""
Script para popular dados clínicos no HAPI FHIR
Cria vacinas, medicamentos, exames e atendimentos para todos os pacientes
"""

import requests
import random
from datetime import datetime, timedelta

FHIR_URL = 'http://localhost:8080/fhir'

# Buscar todos os pacientes
print('Buscando pacientes...')
resp = requests.get(f'{FHIR_URL}/Patient?_count=100')
patients = [e['resource'] for e in resp.json().get('entry', [])]
print(f'Encontrados {len(patients)} pacientes')

# Vacinas para criar
vaccines = [
    {'code': '08', 'display': 'Hepatite B', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '03', 'display': 'MMR (Sarampo, Caxumba, Rubeola)', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '21', 'display': 'Varicela', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '33', 'display': 'Pneumococica', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '52', 'display': 'Hepatite A', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '140', 'display': 'Influenza (Gripe)', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '207', 'display': 'COVID-19 Pfizer', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '208', 'display': 'COVID-19 Moderna', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '115', 'display': 'Tdap (Tetano, Difteria, Coqueluche)', 'system': 'http://hl7.org/fhir/sid/cvx'},
    {'code': '10', 'display': 'Poliomielite', 'system': 'http://hl7.org/fhir/sid/cvx'},
]

# Medicamentos
medications = [
    {'code': '197361', 'display': 'Losartana 50mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '310798', 'display': 'Metformina 850mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '314076', 'display': 'Omeprazol 20mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '866514', 'display': 'Sinvastatina 20mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '197517', 'display': 'AAS 100mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '198211', 'display': 'Atenolol 50mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '151110', 'display': 'Dipirona 500mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
    {'code': '161', 'display': 'Paracetamol 750mg', 'system': 'http://www.nlm.nih.gov/research/umls/rxnorm'},
]

# Exames
exams = [
    {'code': '2093-3', 'display': 'Colesterol Total', 'unit': 'mg/dL', 'min': 150, 'max': 250},
    {'code': '2571-8', 'display': 'Triglicerides', 'unit': 'mg/dL', 'min': 80, 'max': 200},
    {'code': '2345-7', 'display': 'Glicemia de Jejum', 'unit': 'mg/dL', 'min': 70, 'max': 130},
    {'code': '718-7', 'display': 'Hemoglobina', 'unit': 'g/dL', 'min': 12, 'max': 17},
    {'code': '787-2', 'display': 'Hematocrito', 'unit': '%', 'min': 35, 'max': 50},
    {'code': '6690-2', 'display': 'Leucocitos', 'unit': '10*3/uL', 'min': 4, 'max': 11},
    {'code': '2160-0', 'display': 'Creatinina', 'unit': 'mg/dL', 'min': 0.6, 'max': 1.3},
    {'code': '3094-0', 'display': 'Ureia', 'unit': 'mg/dL', 'min': 15, 'max': 45},
]

dosage_options = ['de manha', 'a noite', '2x ao dia', '3x ao dia']
reason_options = ['Consulta de rotina', 'Acompanhamento', 'Exames periodicos', 'Queixa de dor', 'Renovacao de receita']

count_imm = 0
count_med = 0
count_obs = 0
count_enc = 0

for patient in patients[:30]:  # Limitar a 30 para ser rapido
    patient_id = patient['id']
    patient_name = patient.get('name', [{}])[0].get('given', [''])[0] if patient.get('name') else 'Paciente'
    print(f'Populando dados para {patient_name} ({patient_id})...')
    
    # Criar 3-5 vacinas aleatorias
    for vac in random.sample(vaccines, min(random.randint(3, 5), len(vaccines))):
        days_ago = random.randint(30, 1000)
        imm = {
            'resourceType': 'Immunization',
            'status': 'completed',
            'vaccineCode': {
                'coding': [vac]
            },
            'patient': {'reference': f'Patient/{patient_id}'},
            'occurrenceDateTime': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT10:00:00Z'),
            'lotNumber': f'LOT{random.randint(10000, 99999)}',
            'site': {
                'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v3-ActSite', 'code': 'LA', 'display': 'Braco Esquerdo'}]
            },
            'performer': [{'actor': {'display': 'Enfermeira Ana'}}]
        }
        requests.post(f'{FHIR_URL}/Immunization', json=imm)
        count_imm += 1
    
    # Criar 2-4 medicamentos
    for med in random.sample(medications, min(random.randint(2, 4), len(medications))):
        dosage = random.choice(dosage_options)
        med_req = {
            'resourceType': 'MedicationRequest',
            'status': random.choice(['active', 'active', 'completed']),
            'intent': 'order',
            'medicationCodeableConcept': {
                'coding': [med]
            },
            'subject': {'reference': f'Patient/{patient_id}'},
            'authoredOn': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%dT09:00:00Z'),
            'requester': {'display': 'Dr. Carlos Silva'},
            'dosageInstruction': [{
                'text': f'Tomar 1 comprimido {dosage}',
                'timing': {'repeat': {'frequency': random.choice([1, 2, 3]), 'period': 1, 'periodUnit': 'd'}},
                'route': {'coding': [{'code': 'PO', 'display': 'Via Oral'}]}
            }]
        }
        requests.post(f'{FHIR_URL}/MedicationRequest', json=med_req)
        count_med += 1
    
    # Criar exames de laboratorio (Observations)
    for exam in random.sample(exams, min(random.randint(4, 6), len(exams))):
        days_ago = random.randint(1, 90)
        obs = {
            'resourceType': 'Observation',
            'status': 'final',
            'category': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/observation-category', 'code': 'laboratory'}]}],
            'code': {'coding': [{'system': 'http://loinc.org', 'code': exam['code'], 'display': exam['display']}]},
            'subject': {'reference': f'Patient/{patient_id}'},
            'effectiveDateTime': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT08:30:00Z'),
            'valueQuantity': {
                'value': round(random.uniform(exam['min'], exam['max']), 1),
                'unit': exam['unit'],
                'system': 'http://unitsofmeasure.org'
            }
        }
        requests.post(f'{FHIR_URL}/Observation', json=obs)
        count_obs += 1
    
    # Criar 2-3 atendimentos
    encounter_types = [
        {'code': 'AMB', 'display': 'Consulta Ambulatorial'},
        {'code': 'EMER', 'display': 'Emergencia'},
        {'code': 'HH', 'display': 'Atend. Domiciliar'},
        {'code': 'IMP', 'display': 'Internacao'},
    ]
    for _ in range(random.randint(2, 3)):
        days_ago = random.randint(1, 365)
        enc_type = random.choice(encounter_types)
        reason = random.choice(reason_options)
        enc = {
            'resourceType': 'Encounter',
            'status': 'finished',
            'class': {'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode', 'code': enc_type['code'], 'display': enc_type['display']},
            'type': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/encounter-type', 'code': enc_type['code'], 'display': enc_type['display']}]}],
            'subject': {'reference': f'Patient/{patient_id}'},
            'period': {
                'start': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT09:00:00Z'),
                'end': (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT10:30:00Z')
            },
            'reasonCode': [{'text': reason}],
            'participant': [{'individual': {'display': 'Dr. Carlos Silva'}}]
        }
        requests.post(f'{FHIR_URL}/Encounter', json=enc)
        count_enc += 1

print(f'\n=== RESUMO ===')
print(f'Vacinas criadas: {count_imm}')
print(f'Medicamentos criados: {count_med}')
print(f'Exames criados: {count_obs}')
print(f'Atendimentos criados: {count_enc}')
print(f'TOTAL: {count_imm + count_med + count_obs + count_enc} recursos')
