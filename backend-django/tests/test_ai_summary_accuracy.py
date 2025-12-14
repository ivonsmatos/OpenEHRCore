"""
Testes para validar a acurácia e completude dos resumos clínicos gerados pela IA.
Garante que os resumos ajudem profissionais a tomar decisões assertivas.
"""
import pytest
from fhir_api.services.ai_service import AIService


class TestAISummaryAccuracy:
    """Testes de acurácia e completude dos resumos clínicos."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.ai_service = AIService()
    
    def test_simple_patient_summary(self):
        """Testa resumo de paciente simples sem comorbidades."""
        patient_data = {
            'name': 'João Silva',
            'age': 45,
            'gender': 'male',
            'conditions': [],
            'medications': [],
            'vital_signs': [
                {
                    'code': {
                        'coding': [{'code': '8867-4', 'display': 'Heart Rate'}],
                        'text': 'Frequência Cardíaca'
                    },
                    'valueQuantity': {'value': 72, 'unit': 'bpm'}
                },
                {
                    'code': {
                        'coding': [{'code': '8480-6', 'display': 'Systolic BP'}],
                        'text': 'PA Sistólica'
                    },
                    'valueQuantity': {'value': 120, 'unit': 'mmHg'}
                }
            ]
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Verificações básicas
        assert summary is not None
        assert len(summary) > 50, "Resumo muito curto"
        assert 'João Silva' in summary or 'Paciente' in summary
        assert '45' in summary or 'anos' in summary
        
        # Deve mencionar que não há condições registradas
        assert 'diagnóstico' in summary.lower() or 'condição' in summary.lower()
        
    def test_complex_patient_with_comorbidities(self):
        """Testa resumo de paciente complexo com múltiplas comorbidades."""
        patient_data = {
            'name': 'Maria Santos',
            'age': 68,
            'gender': 'female',
            'conditions': [
                {
                    'code': {
                        'coding': [{'code': 'E11', 'display': 'Diabetes Mellitus tipo 2'}],
                        'text': 'Diabetes Mellitus tipo 2'
                    },
                    'clinicalStatus': {
                        'coding': [{'code': 'active'}]
                    }
                },
                {
                    'code': {
                        'coding': [{'code': 'I10', 'display': 'Hipertensão Arterial'}],
                        'text': 'Hipertensão Arterial'
                    },
                    'clinicalStatus': {
                        'coding': [{'code': 'active'}]
                    }
                },
                {
                    'code': {
                        'coding': [{'code': 'I50', 'display': 'Insuficiência Cardíaca'}],
                        'text': 'Insuficiência Cardíaca'
                    },
                    'clinicalStatus': {
                        'coding': [{'code': 'active'}]
                    }
                },
                {
                    'code': {
                        'coding': [{'code': 'N18', 'display': 'Doença Renal Crônica'}],
                        'text': 'Doença Renal Crônica'
                    },
                    'clinicalStatus': {
                        'coding': [{'code': 'active'}]
                    }
                }
            ],
            'medications': [
                {'medicationCodeableConcept': {'text': 'Metformina 850mg'}},
                {'medicationCodeableConcept': {'text': 'Losartana 50mg'}},
                {'medicationCodeableConcept': {'text': 'Furosemida 40mg'}},
                {'medicationCodeableConcept': {'text': 'Carvedilol 6.25mg'}},
                {'medicationCodeableConcept': {'text': 'AAS 100mg'}},
                {'medicationCodeableConcept': {'text': 'Sinvastatina 20mg'}}
            ],
            'vital_signs': [
                {
                    'code': {'coding': [{'code': '8480-6'}], 'text': 'PA Sistólica'},
                    'valueQuantity': {'value': 155, 'unit': 'mmHg'}
                },
                {
                    'code': {'coding': [{'code': '8462-4'}], 'text': 'PA Diastólica'},
                    'valueQuantity': {'value': 92, 'unit': 'mmHg'}
                }
            ]
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Verificações de completude
        assert summary is not None
        assert len(summary) > 200, "Resumo de paciente complexo deve ser detalhado"
        
        # Deve mencionar complexidade alta
        assert 'ALTA' in summary or 'complexo' in summary.lower() or 'múltiplas' in summary.lower()
        
        # Deve identificar comorbidades
        assert 'comorbidade' in summary.lower() or 'diagnóstico' in summary.lower()
        
        # Deve alertar sobre polifarmácia (6 medicamentos)
        assert 'polifarmácia' in summary.lower() or 'medicamento' in summary.lower()
        
        # Deve mencionar condições específicas importantes
        conditions_mentioned = 0
        if 'diabetes' in summary.lower():
            conditions_mentioned += 1
        if 'hipertens' in summary.lower():
            conditions_mentioned += 1
        if 'cardíaca' in summary.lower() or 'ic' in summary.lower():
            conditions_mentioned += 1
        
        assert conditions_mentioned >= 2, "Deve mencionar pelo menos 2 condições principais"
        
        # Deve ter alertas clínicos
        assert '⚠️' in summary or '🚨' in summary or 'alerta' in summary.lower()
        
        # Deve ter recomendações
        assert 'recomenda' in summary.lower() or 'avaliar' in summary.lower() or 'verificar' in summary.lower()
        
    def test_hypertensive_patient_alert(self):
        """Testa se alerta sobre hipertensão é gerado corretamente."""
        patient_data = {
            'name': 'Carlos Lima',
            'age': 55,
            'gender': 'male',
            'conditions': [
                {
                    'code': {'text': 'Hipertensão Arterial'},
                    'clinicalStatus': {'coding': [{'code': 'active'}]}
                }
            ],
            'medications': [],
            'vital_signs': [
                {
                    'code': {'coding': [{'code': '8480-6'}], 'text': 'PA Sistólica'},
                    'valueQuantity': {'value': 165, 'unit': 'mmHg'}
                },
                {
                    'code': {'coding': [{'code': '8462-4'}], 'text': 'PA Diastólica'},
                    'valueQuantity': {'value': 105, 'unit': 'mmHg'}
                }
            ]
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve mencionar hipertensão
        assert 'hipertens' in summary.lower()
        
        # Deve alertar sobre PA elevada
        assert '165' in summary or '105' in summary
        
        # Deve ter alerta visual
        assert '⚠️' in summary or '🔴' in summary or '🚨' in summary
        
        # Deve recomendar ação
        assert 'avaliar' in summary.lower() or 'ajuste' in summary.lower() or 'tratamento' in summary.lower()
        
    def test_diabetic_patient_recommendations(self):
        """Testa se recomendações para diabéticos são incluídas."""
        patient_data = {
            'name': 'Ana Paula',
            'age': 52,
            'gender': 'female',
            'conditions': [
                {
                    'code': {'text': 'Diabetes Mellitus tipo 2'},
                    'clinicalStatus': {'coding': [{'code': 'active'}]}
                }
            ],
            'medications': [
                {'medicationCodeableConcept': {'text': 'Metformina 850mg'}}
            ],
            'vital_signs': []
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve mencionar diabetes
        assert 'diabetes' in summary.lower()
        
        # Deve recomendar exames específicos
        assert 'HbA1c' in summary or 'hemoglobina glicada' in summary.lower() or 'fundo de olho' in summary.lower() or 'função renal' in summary.lower()
        
    def test_polypharmacy_alert(self):
        """Testa se alerta de polifarmácia é gerado (≥5 medicamentos)."""
        patient_data = {
            'name': 'José Costa',
            'age': 72,
            'gender': 'male',
            'conditions': [],
            'medications': [
                {'medicationCodeableConcept': {'text': 'Med1'}},
                {'medicationCodeableConcept': {'text': 'Med2'}},
                {'medicationCodeableConcept': {'text': 'Med3'}},
                {'medicationCodeableConcept': {'text': 'Med4'}},
                {'medicationCodeableConcept': {'text': 'Med5'}},
            ],
            'vital_signs': []
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve alertar sobre polifarmácia
        assert 'polifarmácia' in summary.lower() or '5 medicamento' in summary.lower()
        
        # Deve recomendar revisão
        assert 'interação' in summary.lower() or 'revisar' in summary.lower()
        
    def test_high_risk_polypharmacy(self):
        """Testa alerta crítico para ≥8 medicamentos."""
        patient_data = {
            'name': 'Pedro Alves',
            'age': 80,
            'gender': 'male',
            'conditions': [],
            'medications': [
                {'medicationCodeableConcept': {'text': f'Med{i}'}} for i in range(1, 10)
            ],
            'vital_signs': []
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve ter alerta crítico
        assert '🚨' in summary or 'alto risco' in summary.lower() or 'crítico' in summary.lower()
        
    def test_missing_data_alert(self):
        """Testa se ausência de dados críticos é alertada."""
        patient_data = {
            'name': 'Teste Paciente',
            'age': 45,
            'gender': 'male',
            'conditions': [],
            'medications': [],
            'vital_signs': []
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve alertar sobre dados faltantes
        assert 'sem' in summary.lower() or 'nenhum' in summary.lower() or 'não' in summary.lower() or 'incompleto' in summary.lower()
        
        # Deve recomendar coleta de dados
        assert 'anamnese' in summary.lower() or 'registrar' in summary.lower() or 'aferir' in summary.lower()
        
    def test_elderly_preventive_recommendations(self):
        """Testa se recomendações preventivas para idosos são incluídas."""
        patient_data = {
            'name': 'Idoso Teste',
            'age': 70,
            'gender': 'male',
            'conditions': [],
            'medications': [],
            'vital_signs': []
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve recomendar vacinas para idosos
        assert 'vacina' in summary.lower() or 'influenza' in summary.lower() or 'pneumocócica' in summary.lower()
        
    def test_summary_structure(self):
        """Testa se o resumo tem estrutura adequada com seções."""
        patient_data = {
            'name': 'Estrutura Teste',
            'age': 50,
            'gender': 'female',
            'conditions': [
                {
                    'code': {'text': 'Hipertensão'},
                    'clinicalStatus': {'coding': [{'code': 'active'}]}
                }
            ],
            'medications': [
                {'medicationCodeableConcept': {'text': 'Losartana'}}
            ],
            'vital_signs': [
                {
                    'code': {'coding': [{'code': '8480-6'}], 'text': 'PA'},
                    'valueQuantity': {'value': 130, 'unit': 'mmHg'}
                }
            ]
        }
        
        summary = self.ai_service.generate_patient_summary(patient_data)
        
        # Deve ter seções principais (markdown headers ou emojis de seção)
        section_indicators = ['**', '##', '📋', '💊', '🩺', '💓', '📌', '🎯']
        has_sections = any(indicator in summary for indicator in section_indicators)
        assert has_sections, "Resumo deve ter estrutura com seções"
        
        # Deve ter pelo menos 3 seções diferentes
        section_count = sum(1 for indicator in section_indicators if indicator in summary)
        assert section_count >= 3, "Deve ter pelo menos 3 seções"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
