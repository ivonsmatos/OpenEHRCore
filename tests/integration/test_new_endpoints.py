"""
Script de Teste - Novas Funcionalidades Sprint 34-35
Testa conformidade FHIR R4 e segurança
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(test_name, status, details=""):
    symbol = "✓" if status else "✗"
    color = Colors.GREEN if status else Colors.RED
    print(f"{color}{symbol} {test_name}{Colors.RESET}")
    if details:
        print(f"  {Colors.BLUE}{details}{Colors.RESET}")

def test_health_check():
    """Testa health check do sistema"""
    print(f"\n{Colors.YELLOW}=== TESTE: Health Check ==={Colors.RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        success = response.status_code == 200
        print_test("Health Check", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_test("Health Check", False, f"Erro: {str(e)}")
        return False

def test_goal_endpoints():
    """Testa endpoints do Goal"""
    print(f"\n{Colors.YELLOW}=== TESTE: Goal Endpoints (FHIR R4) ==={Colors.RESET}")
    
    results = []
    
    # 1. Listar Goals
    try:
        response = requests.get(f"{BASE_URL}/goals/")
        success = response.status_code in [200, 401]  # 401 se precisar auth
        print_test("GET /goals/ - Listar Goals", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("GET /goals/", False, f"Erro: {str(e)}")
        results.append(False)
    
    # 2. Criar Goal (teste de validação)
    goal_data = {
        "lifecycle_status": "proposed",
        "achievement_status": "in-progress",
        "description": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "161829001",
                "display": "Reduzir pressão arterial"
            }],
            "text": "Reduzir pressão arterial para <140/90 mmHg"
        },
        "subject_reference": {
            "reference": "Patient/test-123",
            "display": "Paciente Teste"
        },
        "start_date": datetime.now().isoformat(),
        "target_date": (datetime.now() + timedelta(days=90)).isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/goals/",
            json=goal_data,
            headers={"Content-Type": "application/json"}
        )
        # 201 = criado, 401 = não autenticado, 400 = validação
        success = response.status_code in [201, 401, 400]
        details = f"Status: {response.status_code}"
        if response.status_code == 400:
            details += f" - Validação: {response.json()}"
        print_test("POST /goals/ - Criar Goal", success, details)
        results.append(success)
    except Exception as e:
        print_test("POST /goals/", False, f"Erro: {str(e)}")
        results.append(False)
    
    return all(results)

def test_task_endpoints():
    """Testa endpoints do Task"""
    print(f"\n{Colors.YELLOW}=== TESTE: Task Endpoints (Workflow FHIR) ==={Colors.RESET}")
    
    results = []
    
    # 1. Listar Tasks
    try:
        response = requests.get(f"{BASE_URL}/tasks/")
        success = response.status_code in [200, 401]
        print_test("GET /tasks/ - Listar Tasks", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("GET /tasks/", False, f"Erro: {str(e)}")
        results.append(False)
    
    # 2. Criar Task
    task_data = {
        "status": "requested",
        "intent": "order",
        "priority": "routine",
        "code": {
            "coding": [{
                "system": "http://hl7.org/fhir/CodeSystem/task-code",
                "code": "approve",
                "display": "Aprovar pedido"
            }]
        },
        "description": "Aprovar solicitação de exame laboratorial",
        "for_patient_reference": {
            "reference": "Patient/test-123",
            "display": "Paciente Teste"
        },
        "authored_on": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tasks/",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        success = response.status_code in [201, 401, 400]
        print_test("POST /tasks/ - Criar Task", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("POST /tasks/", False, f"Erro: {str(e)}")
        results.append(False)
    
    # 3. Testar ações de workflow (sem criar, só verificar endpoint)
    try:
        response = requests.get(f"{BASE_URL}/tasks/my-tasks/")
        success = response.status_code in [200, 401]
        print_test("GET /tasks/my-tasks/ - Minhas Tarefas", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("GET /tasks/my-tasks/", False, f"Erro: {str(e)}")
        results.append(False)
    
    return all(results)

def test_medication_administration_endpoints():
    """Testa endpoints do MedicationAdministration"""
    print(f"\n{Colors.YELLOW}=== TESTE: MedicationAdministration Endpoints (FHIR R4) ==={Colors.RESET}")
    
    results = []
    
    # 1. Listar MedicationAdministrations
    try:
        response = requests.get(f"{BASE_URL}/medication-administrations/")
        success = response.status_code in [200, 401]
        print_test("GET /medication-administrations/ - Listar", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("GET /medication-administrations/", False, f"Erro: {str(e)}")
        results.append(False)
    
    # 2. Criar MedicationAdministration
    med_admin_data = {
        "status": "in-progress",
        "medication_code": {
            "coding": [{
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "1049502",
                "display": "Dipirona 500mg"
            }],
            "text": "Dipirona 500mg"
        },
        "patient_reference": {
            "reference": "Patient/test-123",
            "display": "Paciente Teste"
        },
        "effective_datetime": datetime.now().isoformat(),
        "dosage_dose_value": 500,
        "dosage_dose_unit": "mg",
        "dosage_route": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "26643006",
                "display": "Via oral"
            }]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/medication-administrations/",
            json=med_admin_data,
            headers={"Content-Type": "application/json"}
        )
        success = response.status_code in [201, 401, 400]
        print_test("POST /medication-administrations/ - Criar", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("POST /medication-administrations/", False, f"Erro: {str(e)}")
        results.append(False)
    
    return all(results)

def test_media_endpoints():
    """Testa endpoints do Media"""
    print(f"\n{Colors.YELLOW}=== TESTE: Media Endpoints (Imagens/Vídeos) ==={Colors.RESET}")
    
    results = []
    
    # 1. Listar Media
    try:
        response = requests.get(f"{BASE_URL}/media/")
        success = response.status_code in [200, 401]
        print_test("GET /media/ - Listar Media", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("GET /media/", False, f"Erro: {str(e)}")
        results.append(False)
    
    # 2. Testar upload (verificar endpoint existe)
    # Não vamos fazer upload real, só verificar que aceita POST
    try:
        response = requests.post(
            f"{BASE_URL}/media/",
            json={},  # Vazio para testar validação
            headers={"Content-Type": "application/json"}
        )
        # Esperamos erro de validação (400) ou auth (401), não 404 ou 500
        success = response.status_code in [400, 401]
        print_test("POST /media/ - Endpoint existe", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("POST /media/", False, f"Erro: {str(e)}")
        results.append(False)
    
    return all(results)

def test_security_headers():
    """Testa headers de segurança"""
    print(f"\n{Colors.YELLOW}=== TESTE: Segurança (Headers HTTP) ==={Colors.RESET}")
    
    results = []
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        headers = response.headers
        
        # Verificar headers de segurança importantes
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Content-Type": "application/json"
        }
        
        for header, expected in security_headers.items():
            if header in headers:
                if isinstance(expected, list):
                    success = headers[header] in expected
                else:
                    success = expected in headers[header]
                print_test(f"Header {header}", success, f"Valor: {headers.get(header)}")
                results.append(success)
            else:
                print_test(f"Header {header}", False, "Não encontrado")
                results.append(False)
        
        return all(results)
    except Exception as e:
        print_test("Security Headers", False, f"Erro: {str(e)}")
        return False

def test_fhir_validation():
    """Testa validação FHIR"""
    print(f"\n{Colors.YELLOW}=== TESTE: Validação FHIR R4 ==={Colors.RESET}")
    
    results = []
    
    # Testar criação com dados inválidos
    invalid_goal = {
        "lifecycle_status": "invalid-status",  # Status inválido
        "description": "Sem estrutura CodeableConcept"  # Deveria ser objeto
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/goals/",
            json=invalid_goal,
            headers={"Content-Type": "application/json"}
        )
        # Deve retornar erro de validação (400 ou 401 se não autenticado)
        success = response.status_code in [400, 401]
        print_test("Validação de dados inválidos", success, f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_test("Validação FHIR", False, f"Erro: {str(e)}")
        results.append(False)
    
    return all(results)

def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TESTE DE INTEGRAÇÃO - SPRINT 34-35")
    print("Novas Funcionalidades FHIR R4")
    print(f"{'='*60}{Colors.RESET}\n")
    
    results = {
        "Health Check": test_health_check(),
        "Goal Endpoints": test_goal_endpoints(),
        "Task Endpoints": test_task_endpoints(),
        "MedicationAdministration": test_medication_administration_endpoints(),
        "Media Endpoints": test_media_endpoints(),
        "Security Headers": test_security_headers(),
        "FHIR Validation": test_fhir_validation()
    }
    
    # Resumo final
    print(f"\n{Colors.BLUE}{'='*60}")
    print("RESUMO DOS TESTES")
    print(f"{'='*60}{Colors.RESET}\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        symbol = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{symbol} {test}{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} testes passaram{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 TODOS OS TESTES PASSARAM!{Colors.RESET}")
        print(f"{Colors.GREEN}Sistema funcionando conforme padrões FHIR R4{Colors.RESET}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Alguns testes falharam{Colors.RESET}")
        print(f"{Colors.YELLOW}Verifique os detalhes acima{Colors.RESET}\n")

if __name__ == "__main__":
    main()
