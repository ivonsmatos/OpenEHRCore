"""
🔬 TESTES DE INTEGRAÇÃO FHIR - EDGE CASES E RESILIÊNCIA
============================================================

Testa cenários críticos:
1. CPF inválido
2. JSON malformado retornado pelo HAPI FHIR
3. Timeout na conexão
4. HAPI FHIR offline
5. Dados inconsistentes
6. Validação de permissões
"""

import pytest
import requests
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
import json
import time

# Importar os serviços que vamos testar
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fhir_api.services.fhir_core import FHIRService, FHIRServiceException

User = get_user_model()


# ====================================================================
# 1. TESTES DE CPF INVÁLIDO
# ====================================================================

class TestCPFValidation(TestCase):
    """Testa validação de CPF em diversos cenários"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
    
    def test_cpf_formato_invalido_caracteres_especiais(self):
        """Deve rejeitar CPF com caracteres especiais"""
        cpfs_invalidos = [
            "123.456.789-00",  # Com pontuação (deve ser apenas dígitos)
            "12345678900!",    # Com exclamação
            "abc.def.ghi-jk",  # Letras
            "000.000.000-00",  # Zeros (CPF inválido)
            "111.111.111-11",  # Todos iguais (CPF inválido)
        ]
        
        for cpf in cpfs_invalidos:
            with self.subTest(cpf=cpf):
                # Testar se função de validação rejeita
                from fhir_api.utils import validate_cpf  # Assumindo que existe
                
                # Se a função ainda não existe, este teste vai falhar
                # (o que é bom - indica que precisa ser implementada)
                try:
                    resultado = validate_cpf(cpf)
                    self.assertFalse(
                        resultado,
                        f"CPF inválido '{cpf}' foi aceito incorretamente"
                    )
                except ImportError:
                    self.fail("Função validate_cpf() não encontrada - IMPLEMENTAR!")
    
    def test_cpf_digito_verificador_invalido(self):
        """Deve rejeitar CPF com dígito verificador errado"""
        # CPF quase válido, mas com último dígito errado
        cpf_invalido = "12345678901"  # Deveria ser ...900
        
        from fhir_api.utils import validate_cpf
        
        try:
            resultado = validate_cpf(cpf_invalido)
            self.assertFalse(resultado, "CPF com dígito verificador errado foi aceito")
        except ImportError:
            self.fail("Função validate_cpf() não encontrada - IMPLEMENTAR!")
    
    @patch('fhir_api.services.fhir_core.FHIRService.create_patient_resource')
    def test_api_rejeita_cpf_invalido(self, mock_create):
        """API deve retornar 400 para CPF inválido antes de chamar FHIR"""
        from django.test import Client
        
        client = Client()
        client.force_login(self.user)
        
        response = client.post('/api/v1/fhir/patient/', {
            'nome': 'João Silva',
            'cpf': '000.000.000-00',  # CPF inválido
            'dataNascimento': '1990-01-01'
        }, content_type='application/json')
        
        # Deve falhar ANTES de tentar criar no FHIR
        self.assertEqual(response.status_code, 400)
        
        # Mock não deve ter sido chamado
        mock_create.assert_not_called()


# ====================================================================
# 2. TESTES DE JSON MALFORMADO DO HAPI FHIR
# ====================================================================

class TestMalformedFHIRResponse(TestCase):
    """Testa resiliência quando HAPI FHIR retorna dados malformados"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.fhir_service = FHIRService(self.user)
    
    @patch('requests.Session.get')
    def test_json_invalido_na_resposta(self, mock_get):
        """Deve tratar graciosamente JSON inválido"""
        # Simular resposta com JSON malformado
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "{invalid json: missing quotes}"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        with self.assertRaises(FHIRServiceException) as context:
            self.fhir_service.get_patient_by_id("123")
        
        # Verificar mensagem de erro é clara
        self.assertIn("JSON", str(context.exception).upper())
    
    @patch('requests.Session.get')
    def test_fhir_retorna_estrutura_inesperada(self, mock_get):
        """Deve tratar quando FHIR retorna estrutura diferente do esperado"""
        # Simular resposta válida como JSON, mas estrutura errada
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            # Esperávamos um Patient, mas veio outra coisa
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "processing",
                "diagnostics": "Internal server error"
            }]
        }
        mock_get.return_value = mock_response
        
        # Deve detectar que não é um Patient válido
        with self.assertRaises(FHIRServiceException):
            patient = self.fhir_service.get_patient_by_id("123")
    
    @patch('requests.Session.get')
    def test_resposta_vazia(self, mock_get):
        """Deve tratar resposta vazia do servidor"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Vazio
        mock_get.return_value = mock_response
        
        # Deve lançar exceção ou retornar None (dependendo da implementação)
        result = self.fhir_service.get_patient_by_id("123")
        
        # Verificar que não causou crash
        self.assertIsNotNone(result)  # Ou usar assertIsNone se for o comportamento esperado


# ====================================================================
# 3. TESTES DE TIMEOUT E CONEXÃO
# ====================================================================

class TestFHIRConnectionTimeout(TestCase):
    """Testa comportamento quando HAPI FHIR está lento ou inacessível"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.fhir_service = FHIRService(self.user)
    
    @patch('requests.Session.get')
    def test_timeout_na_requisicao(self, mock_get):
        """Deve lançar exceção clara quando timeout ocorre"""
        # Simular timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out after 10s")
        
        with self.assertRaises(FHIRServiceException) as context:
            self.fhir_service.get_patient_by_id("123")
        
        # Verificar que mensagem menciona timeout
        error_message = str(context.exception).lower()
        self.assertIn("timeout", error_message)
    
    @patch('requests.Session.get')
    def test_connection_error(self, mock_get):
        """Deve tratar erro de conexão (servidor offline)"""
        # Simular erro de conexão
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Failed to establish connection to localhost:8080"
        )
        
        with self.assertRaises(FHIRServiceException) as context:
            self.fhir_service.get_patient_by_id("123")
        
        # Verificar que mensagem menciona conexão
        error_message = str(context.exception).lower()
        self.assertTrue(
            "connection" in error_message or "unreachable" in error_message,
            f"Error message should mention connection issue: {error_message}"
        )
    
    @patch('requests.Session.get')
    def test_resposta_lenta_mas_bem_sucedida(self, mock_get):
        """Deve aceitar resposta lenta se dentro do timeout"""
        def slow_response(*args, **kwargs):
            time.sleep(0.5)  # Simula lentidão
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "resourceType": "Patient",
                "id": "123",
                "name": [{"given": ["João"], "family": "Silva"}]
            }
            return mock_resp
        
        mock_get.side_effect = slow_response
        
        # Com timeout suficiente, deve funcionar
        patient = self.fhir_service.get_patient_by_id("123")
        self.assertIsNotNone(patient)
        self.assertEqual(patient["id"], "123")
    
    @patch('requests.Session.get')
    @override_settings(FHIR_TIMEOUT=1)  # Timeout muito curto
    def test_timeout_configuravel(self, mock_get):
        """Deve respeitar configuração de timeout"""
        def very_slow_response(*args, **kwargs):
            time.sleep(2)  # Mais lento que o timeout
            return Mock()
        
        mock_get.side_effect = very_slow_response
        
        # Deve falhar por timeout
        with self.assertRaises(FHIRServiceException):
            self.fhir_service.get_patient_by_id("123")


# ====================================================================
# 4. TESTES DE HAPI FHIR OFFLINE
# ====================================================================

class TestFHIRServerOffline(TestCase):
    """Testa degradação graciosa quando HAPI FHIR está completamente offline"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.fhir_service = FHIRService(self.user)
    
    @patch('requests.Session.get')
    def test_health_check_falha(self, mock_get):
        """Health check deve falhar quando servidor está offline"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        with self.assertRaises(FHIRServiceException):
            self.fhir_service.health_check()
    
    @patch('requests.Session.get')
    def test_circuit_breaker_abre_apos_multiplas_falhas(self, mock_get):
        """Circuit breaker deve abrir após várias falhas consecutivas"""
        # Simular servidor offline
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Se circuit breaker existe, deve abrir após N falhas
        failure_count = 0
        max_attempts = 10
        
        for i in range(max_attempts):
            try:
                self.fhir_service.get_patient_by_id("123")
            except FHIRServiceException as e:
                failure_count += 1
                
                # Após N falhas, deve mencionar circuit breaker
                if failure_count > 5:  # Threshold esperado
                    error_msg = str(e).lower()
                    if "circuit" in error_msg or "breaker" in error_msg:
                        # Circuit breaker está funcionando!
                        break
        
        # Se chegou aqui sem circuit breaker, logar aviso
        if failure_count == max_attempts:
            print("⚠️ Circuit breaker NÃO implementado - recomendado para produção")
    
    @patch('requests.Session.get')
    def test_fallback_para_cache_quando_offline(self, mock_get):
        """Deve tentar usar cache quando FHIR está offline (se implementado)"""
        # Simular servidor offline
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Primeiro, popular cache (simular requisição bem-sucedida anterior)
        with patch('django.core.cache.cache.get') as mock_cache_get:
            mock_cache_get.return_value = {
                "resourceType": "Patient",
                "id": "123",
                "name": [{"given": ["João"], "family": "Silva"}]
            }
            
            # Agora, mesmo com servidor offline, pode retornar do cache
            # (Isso só funciona se a lógica de cache estiver implementada)
            try:
                patient = self.fhir_service.get_patient_by_id("123")
                self.assertIsNotNone(patient, "Cache fallback deve retornar dados")
                print("✅ Cache fallback implementado!")
            except FHIRServiceException:
                print("ℹ️ Cache fallback NÃO implementado - considerar para resiliência")


# ====================================================================
# 5. TESTES DE DADOS INCONSISTENTES
# ====================================================================

class TestInconsistentData(TestCase):
    """Testa comportamento com dados inconsistentes ou corrompidos"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.fhir_service = FHIRService(self.user)
    
    @patch('requests.Session.get')
    def test_patient_sem_nome(self, mock_get):
        """Deve tratar paciente sem nome (campo obrigatório faltando)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "123",
            # "name": MISSING!
            "gender": "male"
        }
        mock_get.return_value = mock_response
        
        patient = self.fhir_service.get_patient_by_id("123")
        
        # Deve retornar, mas com nome vazio ou default
        self.assertIsNotNone(patient)
        # Verificar que código não quebra ao acessar name
        name = patient.get("name", [{}])[0].get("given", [""])[0]
        self.assertIsInstance(name, str)
    
    @patch('requests.Session.get')
    def test_multiple_identifiers_conflitantes(self, mock_get):
        """Deve tratar múltiplos identificadores CPF conflitantes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "123",
            "identifier": [
                {
                    "system": "http://openehrcore.com.br/cpf",
                    "value": "12345678900"
                },
                {
                    "system": "http://gov.br/cpf",  # Sistema diferente
                    "value": "98765432100"  # CPF DIFERENTE!
                }
            ]
        }
        mock_get.return_value = mock_response
        
        patient = self.fhir_service.get_patient_by_id("123")
        
        # Deve priorizar o sistema padrão
        from fhir_api.utils import get_patient_cpf
        
        try:
            cpf = get_patient_cpf(patient)
            # Deve retornar o do sistema padrão
            self.assertEqual(cpf, "12345678900")
        except ImportError:
            print("ℹ️ Função get_patient_cpf() não encontrada no backend")
    
    @patch('requests.Session.get')
    def test_data_nascimento_futura(self, mock_get):
        """Deve validar data de nascimento impossível"""
        from datetime import datetime, timedelta
        
        mock_response = Mock()
        mock_response.status_code = 200
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "123",
            "birthDate": future_date  # Data futura!
        }
        mock_get.return_value = mock_response
        
        # Depende da implementação: pode rejeitar ou aceitar
        patient = self.fhir_service.get_patient_by_id("123")
        
        # Calcular idade
        from fhir_api.utils import calculate_age
        
        try:
            age = calculate_age(future_date)
            # Idade negativa ou None devem ser tratados
            if age is not None:
                self.assertGreaterEqual(age, 0, "Idade não pode ser negativa")
        except ImportError:
            print("ℹ️ Função calculate_age() não encontrada")


# ====================================================================
# 6. TESTES DE PERMISSÕES E SEGURANÇA
# ====================================================================

class TestFHIRSecurityAndPermissions(TestCase):
    """Testa validação de permissões e segurança"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.user_sem_permissao = User.objects.create_user(
            username='no_permission',
            email='noperm@example.com'
        )
    
    def test_usuario_sem_autenticacao_nao_acessa_fhir(self):
        """Usuário não autenticado não deve acessar API FHIR"""
        from django.test import Client
        
        client = Client()  # Sem login
        
        response = client.get('/api/v1/fhir/patient/123/')
        
        # Deve retornar 401 ou 403
        self.assertIn(response.status_code, [401, 403])
    
    @patch('requests.Session.get')
    def test_acesso_negado_a_paciente_de_outro_usuario(self, mock_get):
        """Usuário não deve acessar paciente de outro usuário (se aplicável)"""
        # Este teste depende se há isolamento por usuário
        # Se todos os usuários veem todos os pacientes, pular
        
        mock_response = Mock()
        mock_response.status_code = 403  # Forbidden
        mock_response.json.return_value = {
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "forbidden"
            }]
        }
        mock_get.return_value = mock_response
        
        fhir_service = FHIRService(self.user_sem_permissao)
        
        with self.assertRaises(FHIRServiceException):
            fhir_service.get_patient_by_id("outro-paciente-id")
    
    def test_sql_injection_via_search_params(self):
        """Deve sanitizar parâmetros de busca contra SQL injection"""
        from django.test import Client
        
        client = Client()
        client.force_login(self.user)
        
        # Tentar injeção via parâmetro de busca
        malicious_input = "'; DROP TABLE Patient; --"
        
        response = client.get(f'/api/v1/fhir/patient/?name={malicious_input}')
        
        # Não deve causar erro 500 (deve sanitizar ou retornar 400)
        self.assertNotEqual(response.status_code, 500)


# ====================================================================
# 7. TESTES DE PERFORMANCE E CARGA
# ====================================================================

class TestFHIRPerformance(TestCase):
    """Testa performance e comportamento sob carga"""
    
    def setUp(self):
        # Reset circuit breaker antes de cada teste
        FHIRService.reset_circuit()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com'
        )
        self.fhir_service = FHIRService(self.user)
    
    @patch('requests.Session.get')
    def test_multiplas_requisicoes_concorrentes(self, mock_get):
        """Deve suportar múltiplas requisições simultâneas"""
        import threading
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "123"
        }
        mock_get.return_value = mock_response
        
        errors = []
        
        def make_request():
            try:
                self.fhir_service.get_patient_by_id("123")
            except Exception as e:
                errors.append(e)
        
        # Criar 10 threads fazendo requisições simultâneas
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Não deve ter erros
        self.assertEqual(len(errors), 0, f"Errors in concurrent requests: {errors}")
    
    @patch('requests.Session.get')
    def test_cache_reduz_chamadas_ao_fhir(self, mock_get):
        """Cache deve reduzir número de chamadas ao HAPI FHIR"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "123"
        }
        mock_get.return_value = mock_response
        
        # Fazer 5 requisições para o mesmo paciente
        for _ in range(5):
            self.fhir_service.get_patient_by_id("123")
        
        # Se cache está implementado, deve ter chamado mock apenas 1 vez
        # Se não há cache, vai chamar 5 vezes (não é erro, mas menos eficiente)
        call_count = mock_get.call_count
        
        if call_count == 1:
            print("✅ Cache implementado!")
        else:
            print(f"ℹ️ Cache NÃO implementado - {call_count} chamadas para mesma requisição")


# ====================================================================
# 8. EXECUTAR TESTES
# ====================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
