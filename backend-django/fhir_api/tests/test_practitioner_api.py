import pytest
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_fhir_service():
    with patch('fhir_api.views_practitioners.FHIRService') as MockClass:
        service_instance = MagicMock()
        MockClass.return_value = service_instance
        yield service_instance

@pytest.mark.django_db
class TestPractitionerAPI:
    
    def test_list_practitioners_empty(self, auth_client, mock_fhir_service):
        """Testa listagem de profissionais quando não há resultados."""
        # Mock do retorno do FHIRService
        mock_fhir_service.search_resource.return_value = {"resourceType": "Bundle", "total": 0, "entry": []}
        
        response = auth_client.get('/api/v1/practitioners/list/')
        
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['practitioners'] == []
        mock_fhir_service.search_resource.assert_called_with('Practitioner', {})

    def test_create_practitioner_success(self, auth_client, mock_fhir_service):
        """Testa criação bem sucedida de um profissional."""
        data = {
            "family_name": "Silva",
            "given_names": ["João"],
            "prefix": "Dr.",
            "gender": "male",
            "birthDate": "1980-01-01",
            "phone": "11999999999",
            "email": "joao@example.com",
            "crm": "CRM-SP-123456",
            "qualification_code": "MD",
            "qualification_display": "Médico"
        }
        
        # Mock create_resource retorno
        mock_fhir_service.create_resource.return_value = {
            "resourceType": "Practitioner",
            "id": "practitioner-123",
            "name": [{"family": "Silva", "given": ["João"]}]
        }
        
        response = auth_client.post('/api/v1/practitioners/', data, format='json')
        
        assert response.status_code == 201
        assert response.data['id'] == 'practitioner-123'
        
        # Verifica se chamou com os dados corretos (estrutura FHIR)
        args, _ = mock_fhir_service.create_resource.call_args
        resource_type = args[0]
        resource_body = args[1]
        
        assert resource_type == 'Practitioner'
        assert resource_body['name'][0]['family'] == 'Silva'
        assert resource_body['identifier'][0]['value'] == 'CRM-SP-123456'

    def test_create_practitioner_validation_error(self, auth_client):
        """Testa validação de campos obrigatórios."""
        # Payload faltando campos obrigatórios
        data = {
            "family_name": "Silva"
        }
        
        response = auth_client.post('/api/v1/practitioners/', data, format='json')
        
        assert response.status_code == 400
        assert 'given_names' in str(response.data) or 'given_names' in response.data

    def test_get_practitioner_details(self, auth_client, mock_fhir_service):
        """Testa busca de detalhes de um profissional."""
        mock_fhir_service.get_resource.return_value = {
            "resourceType": "Practitioner",
            "id": "123",
            "name": [{"family": "Silva", "given": ["Maria"]}]
        }
        
        response = auth_client.get('/api/v1/practitioners/123/')
        
        assert response.status_code == 200
        assert response.data['id'] == '123'
        mock_fhir_service.get_resource.assert_called_with('Practitioner', '123')
