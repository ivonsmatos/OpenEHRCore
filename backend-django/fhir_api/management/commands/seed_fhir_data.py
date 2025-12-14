"""
Management Command para popular banco de dados com pacientes completos.
Dados 100% FHIR R4 compliant e persistentes.

Uso: python manage.py seed_fhir_data
"""
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import random
import logging

from fhir_api.services.fhir_core import FHIRService, FHIRServiceException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Popula banco de dados com pacientes completos (sinais vitais, diagnósticos, medicamentos, vacinas, exames, agendamentos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=5,
            help='Número de pacientes a criar (padrão: 5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpar dados existentes antes de popular'
        )

    def handle(self, *args, **options):
        num_patients = options['patients']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS(f'\n🎯 Iniciando população do banco de dados...'))
        self.stdout.write(f'   Pacientes a criar: {num_patients}')
        
        if clear_data:
            self.stdout.write(self.style.WARNING('   ⚠️  Modo CLEAR ativado - dados existentes serão removidos'))
        
        try:
            fhir = FHIRService()
            
            # Criar pacientes com dados completos
            for i in range(num_patients):
                self.stdout.write(f'\n📋 Criando paciente {i+1}/{num_patients}...')
                patient_id = self.create_complete_patient(fhir, i)
                
                if patient_id:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Paciente {patient_id} criado com sucesso'))
            
            self.stdout.write(self.style.SUCCESS(f'\n🎉 População concluída! {num_patients} pacientes criados.'))
            self.stdout.write(self.style.SUCCESS('💾 Dados persistidos no banco FHIR Server'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {str(e)}'))
            logger.error(f"Erro ao popular banco: {str(e)}", exc_info=True)

    def create_complete_patient(self, fhir: FHIRService, index: int) -> str:
        """Cria um paciente completo com todos os dados."""
        
        # Dados do paciente
        pacientes_exemplos = [
            {"nome": "Maria Silva Santos", "sexo": "female", "nascimento": "1965-03-15", "cpf": "12345678901"},
            {"nome": "João Pedro Oliveira", "sexo": "male", "nascimento": "1958-07-22", "cpf": "98765432100"},
            {"nome": "Ana Carolina Costa", "sexo": "female", "nascimento": "1972-11-08", "cpf": "45678912300"},
            {"nome": "Carlos Eduardo Lima", "sexo": "male", "nascimento": "1980-05-30", "cpf": "78945612300"},
            {"nome": "Beatriz Rodrigues", "sexo": "female", "nascimento": "1953-09-12", "cpf": "32165498700"},
        ]
        
        paciente = pacientes_exemplos[index % len(pacientes_exemplos)]
        
        try:
            # 1. Criar paciente
            self.stdout.write('   📝 Criando paciente...')
            patient = fhir.create_patient_resource(
                first_name=paciente["nome"].split()[0],
                last_name=" ".join(paciente["nome"].split()[1:]),
                gender=paciente["sexo"],
                birth_date=paciente["nascimento"],
                cpf=paciente["cpf"],
                telecom=[
                    {"system": "phone", "value": f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"},
                    {"system": "email", "value": f"{paciente['nome'].lower().replace(' ', '.')}@email.com"}
                ]
            )
            patient_id = patient.get('id')
            
            # 2. Criar condições (diagnósticos)
            self.stdout.write('   🩺 Criando diagnósticos...')
            conditions = self.create_conditions(fhir, patient_id, index)
            
            # 3. Criar medicamentos
            self.stdout.write('   💊 Criando medicamentos...')
            self.create_medications(fhir, patient_id, conditions)
            
            # 4. Criar sinais vitais (COMPLETOS - múltiplas datas)
            self.stdout.write('   💓 Criando sinais vitais...')
            self.create_vital_signs(fhir, patient_id)
            
            # 5. Criar vacinas
            self.stdout.write('   💉 Criando vacinas...')
            self.create_immunizations(fhir, patient_id)
            
            # 6. Criar exames laboratoriais
            self.stdout.write('   🧪 Criando exames...')
            self.create_diagnostic_reports(fhir, patient_id, conditions)
            
            # 7. Criar agendamentos
            self.stdout.write('   📅 Criando agendamentos...')
            self.create_appointments(fhir, patient_id)
            
            return patient_id
            
        except FHIRServiceException as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro FHIR: {str(e)}'))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
            logger.error(f"Erro ao criar paciente: {str(e)}", exc_info=True)
            return None

    def create_conditions(self, fhir: FHIRService, patient_id: str, index: int) -> list:
        """Cria condições clínicas (diagnósticos)."""
        
        # Perfis de pacientes
        perfis = [
            # Perfil 1: Diabético e Hipertenso (complexidade moderada)
            [
                {"code": "E11.9", "display": "Diabetes Mellitus tipo 2", "status": "active"},
                {"code": "I10", "display": "Hipertensão Arterial Sistêmica", "status": "active"},
            ],
            # Perfil 2: Idoso com múltiplas comorbidades (complexidade alta)
            [
                {"code": "E11.9", "display": "Diabetes Mellitus tipo 2", "status": "active"},
                {"code": "I10", "display": "Hipertensão Arterial Sistêmica", "status": "active"},
                {"code": "I50.0", "display": "Insuficiência Cardíaca", "status": "active"},
                {"code": "N18.3", "display": "Doença Renal Crônica estágio 3", "status": "active"},
                {"code": "I48.0", "display": "Fibrilação Atrial", "status": "active"},
            ],
            # Perfil 3: Paciente com asma
            [
                {"code": "J45.0", "display": "Asma predominantemente alérgica", "status": "active"},
            ],
            # Perfil 4: Paciente com dislipidemia e obesidade
            [
                {"code": "E78.5", "display": "Hiperlipidemia", "status": "active"},
                {"code": "E66.0", "display": "Obesidade", "status": "active"},
            ],
            # Perfil 5: Paciente saudável
            [],
        ]
        
        conditions_list = perfis[index % len(perfis)]
        created_conditions = []
        
        for cond in conditions_list:
            try:
                result = fhir.create_condition_resource(
                    patient_id=patient_id,
                    code=cond["code"],
                    display=cond["display"],
                    clinical_status=cond["status"],
                    onset_date=(datetime.now() - timedelta(days=random.randint(365, 3650))).isoformat()
                )
                created_conditions.append(cond)
            except Exception as e:
                logger.warning(f"Erro ao criar condição {cond['display']}: {str(e)}")
        
        return created_conditions

    def create_medications(self, fhir: FHIRService, patient_id: str, conditions: list):
        """Cria medicamentos baseados nas condições."""
        
        # Mapeamento condição -> medicamentos
        medications_map = {
            "Diabetes": ["Metformina 850mg", "Glibenclamida 5mg", "Insulina NPH"],
            "Hipertensão": ["Losartana 50mg", "Hidroclorotiazida 25mg", "Anlodipino 5mg"],
            "Insuficiência Cardíaca": ["Carvedilol 25mg", "Furosemida 40mg", "Espironolactona 25mg"],
            "Doença Renal": ["Eritropoetina"],
            "Fibrilação Atrial": ["Varfarina 5mg", "Rivaroxabana 20mg"],
            "Asma": ["Salbutamol inalatório", "Budesonida inalatória"],
            "Hiperlipidemia": ["Sinvastatina 40mg", "Atorvastatina 20mg"],
        }
        
        medications_to_create = set()
        medications_to_create.add("AAS 100mg")  # Sempre adicionar AAS
        
        for cond in conditions:
            for key, meds in medications_map.items():
                if key.lower() in cond["display"].lower():
                    medications_to_create.update(random.sample(meds, min(2, len(meds))))
        
        for med_name in medications_to_create:
            try:
                fhir.create_medication_request_resource(
                    patient_id=patient_id,
                    medication_name=med_name,
                    dosage_text="Conforme prescrição",
                    status="active"
                )
            except Exception as e:
                logger.warning(f"Erro ao criar medicamento {med_name}: {str(e)}")

    def create_vital_signs(self, fhir: FHIRService, patient_id: str):
        """Cria múltiplos registros de sinais vitais."""
        
        # Criar 15 registros (últimos 3 meses, ~1 por semana)
        for i in range(15):
            days_ago = i * 7  # 1 por semana
            observation_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # Valores base com variação
            vital_signs = [
                {
                    "code": "8480-6",
                    "display": "Pressão Arterial Sistólica",
                    "value": random.randint(110, 150),
                    "unit": "mmHg"
                },
                {
                    "code": "8462-4",
                    "display": "Pressão Arterial Diastólica",
                    "value": random.randint(70, 95),
                    "unit": "mmHg"
                },
                {
                    "code": "8867-4",
                    "display": "Frequência Cardíaca",
                    "value": random.randint(60, 100),
                    "unit": "bpm"
                },
                {
                    "code": "8310-5",
                    "display": "Temperatura Corporal",
                    "value": round(random.uniform(36.0, 37.5), 1),
                    "unit": "°C"
                },
                {
                    "code": "2708-6",
                    "display": "Saturação de Oxigênio",
                    "value": random.randint(95, 99),
                    "unit": "%"
                },
                {
                    "code": "9279-1",
                    "display": "Frequência Respiratória",
                    "value": random.randint(12, 20),
                    "unit": "irpm"
                },
                {
                    "code": "29463-7",
                    "display": "Peso Corporal",
                    "value": round(random.uniform(60, 90), 1),
                    "unit": "kg"
                },
                {
                    "code": "8302-2",
                    "display": "Altura",
                    "value": round(random.uniform(1.55, 1.85), 2),
                    "unit": "m"
                },
            ]
            
            for vs in vital_signs:
                try:
                    fhir.create_observation_resource(
                        patient_id=patient_id,
                        code=vs["code"],
                        display=vs["display"],
                        value=vs["value"],
                        unit=vs["unit"],
                        category="vital-signs",
                        effective_datetime=observation_date
                    )
                except Exception as e:
                    logger.warning(f"Erro ao criar sinal vital {vs['display']}: {str(e)}")

    def create_immunizations(self, fhir: FHIRService, patient_id: str):
        """Cria registros de vacinação."""
        
        vaccines = [
            {"code": "01", "name": "BCG", "date": "1970-01-15"},
            {"code": "20", "name": "DTP (Tríplice Bacteriana)", "date": "1970-06-10"},
            {"code": "28", "name": "Hepatite B", "date": "1970-08-20"},
            {"code": "86", "name": "Influenza (Gripe)", "date": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")},
            {"code": "213", "name": "COVID-19 (1ª dose)", "date": "2021-05-10"},
            {"code": "213", "name": "COVID-19 (2ª dose)", "date": "2021-08-15"},
            {"code": "213", "name": "COVID-19 (Reforço)", "date": "2022-03-20"},
            {"code": "33", "name": "Pneumocócica 23-valente", "date": "2020-11-05"},
        ]
        
        for vaccine in vaccines:
            try:
                fhir.create_immunization_resource(
                    patient_id=patient_id,
                    vaccine_code=vaccine["code"],
                    vaccine_name=vaccine["name"],
                    date=vaccine["date"],
                    lot_number=f"LOT{random.randint(1000, 9999)}",
                    status="completed"
                )
            except Exception as e:
                logger.warning(f"Erro ao criar vacina {vaccine['name']}: {str(e)}")

    def create_diagnostic_reports(self, fhir: FHIRService, patient_id: str, conditions: list):
        """Cria exames laboratoriais."""
        
        # Exame 1: Hemograma Completo
        try:
            hemograma_date = (datetime.now() - timedelta(days=30)).isoformat()
            fhir.create_diagnostic_report_resource(
                patient_id=patient_id,
                code="58410-2",
                name="Hemograma Completo",
                date=hemograma_date,
                conclusion="Hemograma dentro dos padrões de normalidade. Hemoglobina: 14.2 g/dL, Leucócitos: 7500/mm³, Plaquetas: 250000/mm³"
            )
        except Exception as e:
            logger.warning(f"Erro ao criar hemograma: {str(e)}")
        
        # Exame 2: Glicemia (se diabético)
        if any("Diabetes" in c["display"] for c in conditions):
            try:
                glicemia_date = (datetime.now() - timedelta(days=15)).isoformat()
                fhir.create_diagnostic_report_resource(
                    patient_id=patient_id,
                    code="2339-0",
                    name="Glicemia de Jejum",
                    date=glicemia_date,
                    conclusion=f"Glicemia: {random.randint(90, 140)} mg/dL. HbA1c: {round(random.uniform(6.0, 7.5), 1)}%"
                )
            except Exception as e:
                logger.warning(f"Erro ao criar glicemia: {str(e)}")
        
        # Exame 3: Lipidograma (se hiperlipidemia)
        if any("Hiperlipidemia" in c["display"] for c in conditions):
            try:
                lipido_date = (datetime.now() - timedelta(days=45)).isoformat()
                fhir.create_diagnostic_report_resource(
                    patient_id=patient_id,
                    code="24331-1",
                    name="Lipidograma",
                    date=lipido_date,
                    conclusion=f"Colesterol Total: {random.randint(180, 240)} mg/dL, LDL: {random.randint(100, 160)} mg/dL, HDL: {random.randint(40, 70)} mg/dL, Triglicerídeos: {random.randint(100, 200)} mg/dL"
                )
            except Exception as e:
                logger.warning(f"Erro ao criar lipidograma: {str(e)}")
        
        # Exame 4: Função Renal (se DRC)
        if any("Renal" in c["display"] for c in conditions):
            try:
                renal_date = (datetime.now() - timedelta(days=20)).isoformat()
                fhir.create_diagnostic_report_resource(
                    patient_id=patient_id,
                    code="2160-0",
                    name="Creatinina",
                    date=renal_date,
                    conclusion=f"Creatinina: {round(random.uniform(1.0, 2.0), 1)} mg/dL, TFG: {random.randint(40, 60)} mL/min/1.73m²"
                )
            except Exception as e:
                logger.warning(f"Erro ao criar função renal: {str(e)}")

    def create_appointments(self, fhir: FHIRService, patient_id: str):
        """Cria agendamentos (passados e futuros)."""
        
        appointments = [
            # Consultas passadas
            {"days": -30, "status": "fulfilled", "description": "Consulta de rotina"},
            {"days": -90, "status": "fulfilled", "description": "Retorno"},
            
            # Consultas futuras
            {"days": 15, "status": "booked", "description": "Consulta de acompanhamento"},
            {"days": 45, "status": "booked", "description": "Revisão de exames"},
        ]
        
        for appt in appointments:
            try:
                appt_date = datetime.now() + timedelta(days=appt["days"])
                start_time = appt_date.replace(hour=random.randint(8, 17), minute=random.choice([0, 30]))
                end_time = start_time + timedelta(minutes=30)
                
                fhir.create_appointment_resource(
                    patient_id=patient_id,
                    status=appt["status"],
                    description=appt["description"],
                    start=start_time.isoformat(),
                    end=end_time.isoformat()
                )
            except Exception as e:
                logger.warning(f"Erro ao criar agendamento: {str(e)}")
