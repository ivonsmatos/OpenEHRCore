
import random
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from faker import Faker
from fhir_api.services.fhir_core import FHIRService

class Command(BaseCommand):
    help = 'Popula o servidor FHIR com dados sintéticos (pt-BR)'

    def add_arguments(self, parser):
        parser.add_argument('--patients', type=int, default=10, help='Número de pacientes a gerar')
        parser.add_argument('--clear', action='store_true', help='Limpar dados existentes antes de gerar')

    def handle(self, *args, **options):
        fake = Faker('pt_BR')
        service = FHIRService()
        count = options['patients']

        # Condições comuns (CID-10 simulado)
        COMMON_CONDITIONS = [
            {'code': 'I10', 'display': 'Hipertensão essencial (primária)'},
            {'code': 'E11', 'display': 'Diabetes mellitus não-insulinodependente'},
            {'code': 'J00', 'display': 'Nasofaringite aguda [resfriado comum]'},
            {'code': 'K21', 'display': 'Doença de refluxo gastroesofágico'},
            {'code': 'M54.5', 'display': 'Dor lombar baixa'},
            {'code': 'G43', 'display': 'Enxaqueca'},
            {'code': 'F41.1', 'display': 'Ansiedade generalizada'},
            {'code': 'Z76.0', 'display': 'Emissão de prescrição de repetição'}, 
        ]

        self.stdout.write(self.style.SUCCESS(f'Iniciando geração de dados para {count} pacientes...'))

        for i in range(count):
            try:
                # 1. Gerar Paciente
                profile = fake.simple_profile()
                gender = 'male' if profile['sex'] == 'M' else 'female'
                name = profile['name']
                name_parts = name.split(' ')
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Silva'
                birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
                cpf = fake.cpf()
                
                patient = service.create_patient_resource(
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    birth_date=birth_date,
                    telecom=[{'system': 'phone', 'value': fake.phone_number()}],
                    cpf=cpf
                )
                
                pid = patient.get('id')
                self.stdout.write(f"[{i+1}/{count}] Paciente criado: {name} (ID: {pid})")

                # 2. Gerar Histórico de Atendimentos (Encounters)
                for _ in range(random.randint(1, 4)):
                    past_date = fake.date_time_between(start_date='-1y', end_date='now')
                    encounter_type = random.choice(['ambulatorial', 'urgencia', 'checkup'])
                    
                    service.create_encounter_resource(
                        patient_id=pid,
                        status='finished',
                        encounter_type=encounter_type, # Using directly
                        period_start=past_date.isoformat(),
                        period_end=(past_date + timedelta(minutes=30)).isoformat()
                    )

                # 3. Gerar Condições Ativas (Conditions)
                if random.random() > 0.3: 
                    conditions = random.sample(COMMON_CONDITIONS, k=random.randint(1, 2))
                    for cond in conditions:
                        service.create_condition_resource(
                            patient_id=pid,
                            code=cond['code'],
                            display=cond['display'],
                            clinical_status='active'
                        )

                # 4. Gerar Agendamentos Futuros (Appointments)
                if random.random() > 0.5:
                    future_date = fake.date_time_between(start_date='now', end_date='+2d')
                    service.create_appointment_resource(
                        patient_id=pid,
                        status='booked',
                        description='Consulta de Rotina',
                        start=future_date.isoformat(),
                        end=(future_date + timedelta(minutes=30)).isoformat()
                    )

                # 5. Gerar Sinais Vitais (Observations)
                service.create_observation_resource(
                    patient_id=pid,
                    category='vital-signs',
                    code='8867-4',
                    display='Heart rate',
                    value=random.randint(60, 100),
                    unit='bpm',
                    effective_date=datetime.now().isoformat()
                )
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao gerar paciente {i+1}: {e}"))
                import traceback
                traceback.print_exc()

        self.stdout.write(self.style.SUCCESS('Geração de dados concluída!'))
