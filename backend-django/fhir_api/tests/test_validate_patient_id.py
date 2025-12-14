"""
🧪 Testes para validate_patient_id
====================================

Testa a nova função que aceita tanto UUID quanto IDs numéricos.
"""

import pytest
from fhir_api.utils.validators import validate_patient_id


class TestValidatePatientId:
    """Testes para validação de patient_id (UUID ou numérico)"""
    
    def test_valid_uuid(self):
        """Aceita UUIDs válidos"""
        assert validate_patient_id('550e8400-e29b-41d4-a716-446655440000')
        assert validate_patient_id('123e4567-e89b-12d3-a456-426614174000')
        assert validate_patient_id('AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE')
    
    def test_valid_numeric_ids(self):
        """Aceita IDs numéricos válidos"""
        assert validate_patient_id('1')
        assert validate_patient_id('8')
        assert validate_patient_id('42')
        assert validate_patient_id('123')
        assert validate_patient_id('12345678901234567890')  # 20 dígitos (máximo)
    
    def test_invalid_empty_string(self):
        """Rejeita string vazia"""
        assert not validate_patient_id('')
        assert not validate_patient_id('   ')
    
    def test_invalid_none(self):
        """Rejeita None"""
        assert not validate_patient_id(None)
    
    def test_invalid_sql_injection(self):
        """Rejeita tentativas de SQL injection"""
        assert not validate_patient_id("'; DROP TABLE patients; --")
        assert not validate_patient_id("1 OR 1=1")
        assert not validate_patient_id("admin'--")
    
    def test_invalid_special_characters(self):
        """Rejeita IDs com caracteres especiais (exceto UUID)"""
        assert not validate_patient_id('abc123')
        assert not validate_patient_id('patient-123')
        assert not validate_patient_id('123.456')
        assert not validate_patient_id('123/456')
    
    def test_invalid_too_long_numeric(self):
        """Rejeita IDs numéricos muito longos (>20 dígitos)"""
        assert not validate_patient_id('123456789012345678901')  # 21 dígitos
    
    def test_invalid_malformed_uuid(self):
        """Rejeita UUIDs malformados"""
        assert not validate_patient_id('550e8400-e29b-41d4-a716')  # Incompleto
        assert not validate_patient_id('550e8400e29b41d4a716446655440000')  # Sem hífens
        assert not validate_patient_id('not-a-uuid-at-all')
    
    def test_whitespace_handling(self):
        """Remove espaços em branco e valida"""
        assert validate_patient_id('  8  ')
        assert validate_patient_id('  550e8400-e29b-41d4-a716-446655440000  ')
    
    def test_mixed_case_uuid(self):
        """Aceita UUIDs em qualquer case"""
        assert validate_patient_id('550E8400-E29B-41D4-A716-446655440000')
        assert validate_patient_id('550e8400-E29B-41d4-A716-446655440000')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
