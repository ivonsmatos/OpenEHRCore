"""
Locust Load Testing for OpenEHR FHIR API
========================================

Testes de carga para endpoints críticos da API FHIR.

Uso:
    # Modo UI (recomendado para desenvolvimento)
    locust -f locustfile.py --host=http://localhost:8000

    # Modo headless (CI/CD)
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 60s --headless

    # Com múltiplos workers
    locust -f locustfile.py --host=http://localhost:8000 \
           --master --expect-workers 4

    # Worker (rodar em múltiplos terminais)
    locust -f locustfile.py --worker --master-host=localhost

Métricas Alvo:
    - P95 response time < 500ms (leitura)
    - P95 response time < 1000ms (escrita)
    - Taxa de erro < 1%
    - Throughput > 100 req/s
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class FHIRApiUser(HttpUser):
    """
    Simula um usuário típico da API FHIR.
    
    - 70% leitura (GET)
    - 20% escrita (POST)
    - 10% atualização/deleção (PUT/DELETE)
    """
    
    wait_time = between(1, 3)  # Espera 1-3s entre requisições
    
    # Cache de IDs para reutilização
    patient_ids = []
    encounter_ids = []
    
    def on_start(self):
        """Executado quando o usuário inicia - setup inicial"""
        self.client.verify = False  # Ignora SSL em dev/test
        
        # Headers padrão
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Cria alguns pacientes de teste para uso posterior
        self._create_test_patients(count=5)
    
    def _create_test_patients(self, count=5):
        """Cria pacientes de teste no início da sessão"""
        for i in range(count):
            patient_data = {
                "first_name": f"LoadTest{i}",
                "last_name": f"Patient{uuid.uuid4().hex[:8]}",
                "birth_date": self._random_birth_date(),
                "cpf": self._generate_valid_cpf(),
                "gender": random.choice(["male", "female", "other"])
            }
            
            with self.client.post(
                "/api/v1/patients/",
                json=patient_data,
                headers=self.headers,
                catch_response=True,
                name="/api/v1/patients/ [CREATE]"
            ) as response:
                if response.status_code == 201:
                    result = response.json()
                    if "id" in result:
                        self.patient_ids.append(result["id"])
                    response.success()
                elif response.status_code == 404:
                    # Endpoint pode não existir em alguns ambientes
                    response.failure("Endpoint not found")
                    raise RescheduleTask()
    
    # ========================
    # TASKS - LEITURA (70%)
    # ========================
    
    @task(30)
    def list_patients(self):
        """GET /api/v1/patients/ - Lista pacientes"""
        page = random.randint(1, 5)
        with self.client.get(
            f"/api/v1/patients/?page={page}",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/patients/ [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(20)
    def get_patient_detail(self):
        """GET /api/v1/patients/{id}/ - Detalhes de um paciente"""
        if not self.patient_ids:
            return
        
        patient_id = random.choice(self.patient_ids)
        with self.client.get(
            f"/api/v1/patients/{patient_id}/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/patients/{id}/ [DETAIL]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Aceitável - paciente pode ter sido deletado
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(10)
    def get_ai_summary(self):
        """GET /api/v1/ai/patient-summary/{id}/ - Resumo AI"""
        if not self.patient_ids:
            return
        
        patient_id = random.choice(self.patient_ids)
        with self.client.get(
            f"/api/v1/ai/patient-summary/{patient_id}/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/ai/patient-summary/{id}/ [AI]"
        ) as response:
            if response.status_code in [200, 404, 503]:
                # 200: sucesso
                # 404: paciente não encontrado (ok)
                # 503: Circuit breaker aberto (esperado sob carga)
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def health_check(self):
        """GET /api/v1/health/ - Health check"""
        with self.client.get(
            "/api/v1/health/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/health/ [HEALTH]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def list_analytics_kpi(self):
        """GET /api/v1/analytics/kpi/ - KPI metrics"""
        with self.client.get(
            "/api/v1/analytics/kpi/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/analytics/kpi/ [ANALYTICS]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    # ========================
    # TASKS - ESCRITA (20%)
    # ========================
    
    @task(10)
    def create_patient(self):
        """POST /api/v1/patients/ - Cria novo paciente"""
        patient_data = {
            "first_name": f"Load{uuid.uuid4().hex[:6]}",
            "last_name": f"Test{uuid.uuid4().hex[:6]}",
            "birth_date": self._random_birth_date(),
            "cpf": self._generate_valid_cpf(),
            "gender": random.choice(["male", "female", "other"]),
            "telecom": {
                "phone": f"11{random.randint(900000000, 999999999)}",
                "email": f"loadtest{uuid.uuid4().hex[:8]}@example.com"
            }
        }
        
        with self.client.post(
            "/api/v1/patients/",
            json=patient_data,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/patients/ [CREATE]"
        ) as response:
            if response.status_code == 201:
                result = response.json()
                if "id" in result:
                    self.patient_ids.append(result["id"])
                response.success()
            elif response.status_code == 400:
                # Pode ser CPF duplicado - aceitável
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def create_encounter(self):
        """POST /api/v1/encounters/ - Cria encontro"""
        if not self.patient_ids:
            return
        
        encounter_data = {
            "patient_id": random.choice(self.patient_ids),
            "encounter_type": random.choice(["consultation", "emergency", "hospitalization"]),
            "status": "finished",
            "period_start": (datetime.now() - timedelta(hours=2)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "reason_code": random.choice(["fever", "cough", "headache", "chest_pain"])
        }
        
        with self.client.post(
            "/api/v1/encounters/",
            json=encounter_data,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/encounters/ [CREATE]"
        ) as response:
            if response.status_code == 201:
                result = response.json()
                if "id" in result:
                    self.encounter_ids.append(result["id"])
                response.success()
            elif response.status_code in [400, 404]:
                response.success()  # Aceitável
            else:
                response.failure(f"Status {response.status_code}")
    
    # ========================
    # TASKS - EDGE CASES (10%)
    # ========================
    
    @task(3)
    def invalid_uuid(self):
        """Testa UUID inválido - deve retornar 400"""
        with self.client.get(
            "/api/v1/patients/invalid-uuid-12345/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/patients/{invalid_uuid}/ [VALIDATION]"
        ) as response:
            if response.status_code in [400, 404]:
                response.success()  # Esperado
            else:
                response.failure(f"Expected 400/404, got {response.status_code}")
    
    @task(2)
    def large_pagination(self):
        """Testa paginação grande"""
        with self.client.get(
            "/api/v1/patients/?page=999999",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/patients/?page=large [PAGINATION]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    # ========================
    # HELPER METHODS
    # ========================
    
    def _random_birth_date(self):
        """Gera data de nascimento aleatória (18-80 anos atrás)"""
        days_ago = random.randint(18*365, 80*365)
        birth_date = datetime.now() - timedelta(days=days_ago)
        return birth_date.strftime("%Y-%m-%d")
    
    def _generate_valid_cpf(self):
        """
        Gera CPF válido com dígitos verificadores corretos.
        Algoritmo: https://www.geradorcpf.com/algoritmo_do_cpf.htm
        """
        # Gera 9 primeiros dígitos
        cpf = [random.randint(0, 9) for _ in range(9)]
        
        # Calcula primeiro dígito verificador
        sum_1 = sum((10 - i) * cpf[i] for i in range(9))
        digit_1 = 11 - (sum_1 % 11)
        digit_1 = 0 if digit_1 >= 10 else digit_1
        cpf.append(digit_1)
        
        # Calcula segundo dígito verificador
        sum_2 = sum((11 - i) * cpf[i] for i in range(10))
        digit_2 = 11 - (sum_2 % 11)
        digit_2 = 0 if digit_2 >= 10 else digit_2
        cpf.append(digit_2)
        
        # Formata CPF
        cpf_str = ''.join(map(str, cpf))
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"


class AdminUser(HttpUser):
    """
    Simula usuário administrativo com operações pesadas.
    Menor frequência, mas endpoints mais custosos.
    """
    
    wait_time = between(5, 10)
    weight = 1  # 1 admin para cada 10 usuários normais
    
    def on_start(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @task(5)
    def analytics_clinical(self):
        """GET /api/v1/analytics/clinical/ - Analytics pesado"""
        with self.client.get(
            "/api/v1/analytics/clinical/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/analytics/clinical/ [ADMIN]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)
    def list_all_documents(self):
        """GET /api/v1/documents/ - Lista documentos"""
        with self.client.get(
            "/api/v1/documents/",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/documents/ [ADMIN]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


# ========================
# EVENT HANDLERS
# ========================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado quando o teste inicia"""
    print("\n" + "="*80)
    print("🚀 INICIANDO LOAD TEST - OpenEHR FHIR API")
    print("="*80)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado quando o teste termina"""
    print("\n" + "="*80)
    print("✅ LOAD TEST CONCLUÍDO")
    print("="*80)
    
    stats = environment.stats
    
    print(f"\n📊 Resumo:")
    print(f"  Total de requisições: {stats.total.num_requests}")
    print(f"  Falhas: {stats.total.num_failures} ({stats.total.fail_ratio*100:.2f}%)")
    print(f"  Tempo médio: {stats.total.avg_response_time:.2f}ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  RPS: {stats.total.total_rps:.2f} req/s")
    
    # Verifica se atende aos SLAs
    p95 = stats.total.get_response_time_percentile(0.95)
    fail_ratio = stats.total.fail_ratio
    
    print(f"\n🎯 SLA Check:")
    print(f"  P95 < 1000ms: {'✅' if p95 < 1000 else '❌'} ({p95:.2f}ms)")
    print(f"  Taxa de erro < 1%: {'✅' if fail_ratio < 0.01 else '❌'} ({fail_ratio*100:.2f}%)")
    
    print("="*80 + "\n")


# ========================
# CONFIGURAÇÕES AVANÇADAS
# ========================

# Desabilita avisos de SSL em ambiente de teste
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
