"""
Django management command para popular dados FHIR com pacientes completos.
Cria recursos diretamente no HAPI FHIR Server.

Uso: python manage.py populate_fhir --patients 3
"""

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import requests
import random


class Command(BaseCommand):
    help = 'Popula FHIR Server com pacientes completos (vitais, diagnósticos, medicamentos, vacinas, exames, agendamentos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=3,
            help='Número de pacientes (padrão: 3)'
        )

    def __init__(self):
        super().__init__()
        self.fhir_url = "http://localhost:8080/fhir"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        })

    def handle(self, *args, **options):
        num_patients = options['patients']
        self.stdout.write(self.style.SUCCESS(f'\n🎯 Iniciando população FHIR...'))
        self.stdout.write(f'   Pacientes: {num_patients}\n')

        # Perfis de pacientes realistas
        patient_profiles = [
            {
                "nome": "João Silva Santos",
                "genero": "male",
                "data_nascimento": "1955-03-15",
                "cpf": "123.456.789-01",
                "telefone": "(11) 98765-4321",
                "condicoes": [
                    {"code": "E11.9", "display": "Diabetes Mellitus tipo 2"},
                    {"code": "I10", "display": "Hipertensão Arterial Sistêmica"}
                ],
                "medicamentos": [
                    {"code": "6809", "display": "Metformina 850mg", "dosagem": "1 comprimido 2x ao dia"},
                    {"code": "52175", "display": "Losartana 50mg", "dosagem": "1 comprimido pela manhã"},
                    {"code": "1191", "display": "Aspirina 100mg", "dosagem": "1 comprimido à noite"}
                ]
            },
            {
                "nome": "Maria Santos Oliveira",
                "genero": "female",
                "data_nascimento": "1978-07-22",
                "cpf": "987.654.321-09",
                "telefone": "(21) 99876-5432",
                "condicoes": [],
                "medicamentos": []
            },
            {
                "nome": "Pedro Oliveira Costa",
                "genero": "male",
                "data_nascimento": "1990-11-10",
                "cpf": "456.789.123-45",
                "telefone": "(31) 91234-5678",
                "condicoes": [
                    {"code": "J45.0", "display": "Asma"}
                ],
                "medicamentos": [
                    {"code": "1649221", "display": "Budesonida/Formoterol 200/6mcg", "dosagem": "2 inalações 2x ao dia"}
                ]
            }
        ]

        created_count = 0
        for i in range(min(num_patients, len(patient_profiles))):
            profile = patient_profiles[i]
            self.stdout.write(f'\n📋 Criando: {profile["nome"]}...')
            
            try:
                # 1. Criar paciente
                patient_id = self.create_patient(profile)
                if not patient_id:
                    continue
                
                self.stdout.write(f'   ✅ Paciente ID: {patient_id}')
                
                # 2. Criar condições
                for cond in profile["condicoes"]:
                    self.create_condition(patient_id, cond["code"], cond["display"])
                self.stdout.write(f'   🩺 Condições: {len(profile["condicoes"])}')
                
                # 3. Criar medicamentos
                for med in profile["medicamentos"]:
                    self.create_medication_request(patient_id, med["code"], med["display"], med["dosagem"])
                self.stdout.write(f'   💊 Medicamentos: {len(profile["medicamentos"])}')
                
                # 4. Criar sinais vitais (15 registros = 75 observations)
                vitals_count = self.create_vital_signs(patient_id)
                self.stdout.write(f'   💓 Sinais vitais: {vitals_count}')
                
                # 5. Criar vacinas
                vaccines_count = self.create_immunizations(patient_id)
                self.stdout.write(f'   💉 Vacinas: {vaccines_count}')
                
                # 6. Criar exames
                exams_count = self.create_diagnostic_reports(patient_id)
                self.stdout.write(f'   🧪 Exames: {exams_count}')
                
                # 7. Criar agendamentos
                appointments_count = self.create_appointments(patient_id, profile["nome"])
                self.stdout.write(f'   📅 Agendamentos: {appointments_count}')
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n\n🎉 Conclusão: {created_count}/{num_patients} pacientes criados!'))

    def create_patient(self, profile):
        """Cria recurso Patient no FHIR"""
        parts = profile["nome"].split()
        first_name = parts[0]
        last_name = " ".join(parts[1:])
        
        patient = {
            "resourceType": "Patient",
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "TAX"
                    }]
                },
                "system": "http://openehrcore.com.br/cpf",
                "value": profile["cpf"]
            }],
            "active": True,
            "name": [{
                "use": "official",
                "family": last_name,
                "given": [first_name]
            }],
            "telecom": [{
                "system": "phone",
                "value": profile["telefone"],
                "use": "mobile"
            }],
            "gender": profile["genero"],
            "birthDate": profile["data_nascimento"]
        }
        
        response = self.session.post(f"{self.fhir_url}/Patient", json=patient)
        if response.status_code == 201:
            return response.json().get("id")
        return None

    def create_condition(self, patient_id, code, display):
        """Cria recurso Condition"""
        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": code,
                    "display": display
                }],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": datetime.now().isoformat()
        }
        
        self.session.post(f"{self.fhir_url}/Condition", json=condition)

    def create_medication_request(self, patient_id, code, display, dosage):
        """Cria recurso MedicationRequest"""
        medication_request = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": code,
                    "display": display
                }],
                "text": display
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "dosageInstruction": [{
                "text": dosage
            }],
            "authoredOn": datetime.now().isoformat()
        }
        
        self.session.post(f"{self.fhir_url}/MedicationRequest", json=medication_request)

    def create_vital_signs(self, patient_id):
        """Cria 15 registros de sinais vitais (75 observations total)"""
        count = 0
        
        # Definir valores base para este paciente
        bp_systolic_base = random.randint(115, 145)
        bp_diastolic_base = random.randint(70, 90)
        hr_base = random.randint(65, 85)
        temp_base = round(random.uniform(36.2, 36.8), 1)
        spo2_base = random.randint(95, 99)
        rr_base = random.randint(14, 18)
        
        for i in range(15):
            # Variar levemente os valores
            days_ago = i * 7  # 1 medição por semana
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # Pressão Arterial (componente)
            bp_observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Pressão Arterial"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": timestamp,
                "component": [
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Sistólica"
                            }]
                        },
                        "valueQuantity": {
                            "value": bp_systolic_base + random.randint(-5, 5),
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    },
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastólica"
                            }]
                        },
                        "valueQuantity": {
                            "value": bp_diastolic_base + random.randint(-3, 3),
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    }
                ]
            }
            
            resp = self.session.post(f"{self.fhir_url}/Observation", json=bp_observation)
            if resp.status_code == 201:
                count += 1
            
            # Frequência Cardíaca
            hr_observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Frequência Cardíaca"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": timestamp,
                "valueQuantity": {
                    "value": hr_base + random.randint(-5, 5),
                    "unit": "bpm",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            }
            
            resp = self.session.post(f"{self.fhir_url}/Observation", json=hr_observation)
            if resp.status_code == 201:
                count += 1
            
            # Temperatura
            temp_observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8310-5",
                        "display": "Temperatura Corporal"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": timestamp,
                "valueQuantity": {
                    "value": round(temp_base + random.uniform(-0.2, 0.2), 1),
                    "unit": "°C",
                    "system": "http://unitsofmeasure.org",
                    "code": "Cel"
                }
            }
            
            resp = self.session.post(f"{self.fhir_url}/Observation", json=temp_observation)
            if resp.status_code == 201:
                count += 1
            
            # Saturação de Oxigênio
            spo2_observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "2708-6",
                        "display": "Saturação de Oxigênio"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": timestamp,
                "valueQuantity": {
                    "value": spo2_base + random.randint(-1, 1),
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%"
                }
            }
            
            resp = self.session.post(f"{self.fhir_url}/Observation", json=spo2_observation)
            if resp.status_code == 201:
                count += 1
            
            # Frequência Respiratória
            rr_observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "9279-1",
                        "display": "Frequência Respiratória"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": timestamp,
                "valueQuantity": {
                    "value": rr_base + random.randint(-2, 2),
                    "unit": "/min",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            }
            
            resp = self.session.post(f"{self.fhir_url}/Observation", json=rr_observation)
            if resp.status_code == 201:
                count += 1
        
        return count

    def create_immunizations(self, patient_id):
        """Cria registros de vacinação"""
        vaccines = [
            {"code": "207", "display": "COVID-19 Pfizer", "date": "2023-06-15"},
            {"code": "88", "display": "Influenza", "date": "2023-04-10"},
            {"code": "33", "display": "Pneumocócica", "date": "2022-08-20"},
            {"code": "45", "display": "Hepatite B", "date": "2020-01-15"}
        ]
        
        count = 0
        for vaccine in vaccines:
            immunization = {
                "resourceType": "Immunization",
                "status": "completed",
                "vaccineCode": {
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": vaccine["code"],
                        "display": vaccine["display"]
                    }]
                },
                "patient": {"reference": f"Patient/{patient_id}"},
                "occurrenceDateTime": vaccine["date"],
                "lotNumber": f"LOT{random.randint(1000, 9999)}"
            }
            
            resp = self.session.post(f"{self.fhir_url}/Immunization", json=immunization)
            if resp.status_code == 201:
                count += 1
        
        return count

    def create_diagnostic_reports(self, patient_id):
        """Cria laudos de exames"""
        reports = [
            {
                "code": "58410-2",
                "display": "Hemograma Completo",
                "conclusion": "Hemácias: 4.5 milhões/mm³. Leucócitos: 7.200/mm³. Plaquetas: 250.000/mm³. Valores dentro da normalidade.",
                "date": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "code": "2093-3",
                "display": "Colesterol Total",
                "conclusion": "Colesterol total: 185 mg/dL. Dentro do valor de referência (< 200 mg/dL).",
                "date": (datetime.now() - timedelta(days=45)).isoformat()
            }
        ]
        
        count = 0
        for report in reports:
            diagnostic_report = {
                "resourceType": "DiagnosticReport",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                        "display": "Laboratório"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": report["code"],
                        "display": report["display"]
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": report["date"],
                "conclusion": report["conclusion"]
            }
            
            resp = self.session.post(f"{self.fhir_url}/DiagnosticReport", json=diagnostic_report)
            if resp.status_code == 201:
                count += 1
        
        return count

    def create_appointments(self, patient_id, patient_name):
        """Cria agendamentos futuros"""
        appointments_data = [
            {
                "description": "Consulta de rotina",
                "days_offset": 3,
                "hour": 10
            },
            {
                "description": "Retorno - acompanhamento",
                "days_offset": 15,
                "hour": 14
            }
        ]
        
        count = 0
        for appt_data in appointments_data:
            start_dt = datetime.now() + timedelta(days=appt_data["days_offset"])
            start_dt = start_dt.replace(hour=appt_data["hour"], minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(minutes=30)
            
            appointment = {
                "resourceType": "Appointment",
                "status": "booked",
                "description": appt_data["description"],
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "participant": [{
                    "actor": {"reference": f"Patient/{patient_id}"},
                    "status": "accepted"
                }],
                "created": datetime.now().isoformat()
            }
            
            resp = self.session.post(f"{self.fhir_url}/Appointment", json=appointment)
            if resp.status_code == 201:
                count += 1
        
        return count
