"""
Demonstração das melhorias nos resumos clínicos gerados pela IA.
Este script mostra exemplos de resumos antes e depois das melhorias.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
import django
django.setup()

from fhir_api.services.ai_service import AIService


def print_separator():
    print("\n" + "="*80 + "\n")


def demo_case_1_simple_patient():
    """Caso 1: Paciente simples sem comorbidades."""
    print("📋 CASO 1: Paciente Simples (Baixa Complexidade)")
    print_separator()
    
    patient_data = {
        'name': 'João da Silva',
        'age': 42,
        'gender': 'male',
        'conditions': [],
        'medications': [],
        'vital_signs': [
            {
                'code': {
                    'coding': [{'code': '8867-4', 'display': 'Heart Rate'}],
                    'text': 'Frequência Cardíaca'
                },
                'valueQuantity': {'value': 75, 'unit': 'bpm'}
            },
            {
                'code': {
                    'coding': [{'code': '8480-6', 'display': 'Systolic BP'}],
                    'text': 'PA Sistólica'
                },
                'valueQuantity': {'value': 125, 'unit': 'mmHg'}
            },
            {
                'code': {
                    'coding': [{'code': '8462-4', 'display': 'Diastolic BP'}],
                    'text': 'PA Diastólica'
                },
                'valueQuantity': {'value': 78, 'unit': 'mmHg'}
            }
        ]
    }
    
    ai_service = AIService()
    summary = ai_service.generate_patient_summary(patient_data)
    
    print(summary)
    print_separator()


def demo_case_2_diabetic_hypertensive():
    """Caso 2: Paciente diabético e hipertenso."""
    print("📋 CASO 2: Paciente Diabético e Hipertenso (Complexidade Moderada)")
    print_separator()
    
    patient_data = {
        'name': 'Maria Santos',
        'age': 58,
        'gender': 'female',
        'conditions': [
            {
                'code': {
                    'coding': [{'code': 'E11', 'display': 'Diabetes Mellitus tipo 2'}],
                    'text': 'Diabetes Mellitus tipo 2'
                },
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            },
            {
                'code': {
                    'coding': [{'code': 'I10', 'display': 'Hipertensão Arterial'}],
                    'text': 'Hipertensão Arterial'
                },
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            }
        ],
        'medications': [
            {'medicationCodeableConcept': {'text': 'Metformina 850mg 2x/dia'}},
            {'medicationCodeableConcept': {'text': 'Losartana 50mg 1x/dia'}},
            {'medicationCodeableConcept': {'text': 'AAS 100mg 1x/dia'}}
        ],
        'vital_signs': [
            {
                'code': {'coding': [{'code': '8480-6'}], 'text': 'PA Sistólica'},
                'valueQuantity': {'value': 145, 'unit': 'mmHg'}
            },
            {
                'code': {'coding': [{'code': '8462-4'}], 'text': 'PA Diastólica'},
                'valueQuantity': {'value': 88, 'unit': 'mmHg'}
            },
            {
                'code': {'coding': [{'code': '8867-4'}], 'text': 'FC'},
                'valueQuantity': {'value': 82, 'unit': 'bpm'}
            }
        ]
    }
    
    ai_service = AIService()
    summary = ai_service.generate_patient_summary(patient_data)
    
    print(summary)
    print_separator()


def demo_case_3_complex_elderly():
    """Caso 3: Paciente idoso com múltiplas comorbidades."""
    print("📋 CASO 3: Paciente Idoso com Múltiplas Comorbidades (Alta Complexidade)")
    print_separator()
    
    patient_data = {
        'name': 'José Carlos Oliveira',
        'age': 72,
        'gender': 'male',
        'conditions': [
            {
                'code': {'text': 'Diabetes Mellitus tipo 2'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            },
            {
                'code': {'text': 'Hipertensão Arterial'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            },
            {
                'code': {'text': 'Insuficiência Cardíaca'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            },
            {
                'code': {'text': 'Doença Renal Crônica'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            },
            {
                'code': {'text': 'Fibrilação Atrial'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            }
        ],
        'medications': [
            {'medicationCodeableConcept': {'text': 'Metformina 850mg'}},
            {'medicationCodeableConcept': {'text': 'Losartana 100mg'}},
            {'medicationCodeableConcept': {'text': 'Furosemida 40mg'}},
            {'medicationCodeableConcept': {'text': 'Carvedilol 25mg'}},
            {'medicationCodeableConcept': {'text': 'Varfarina 5mg'}},
            {'medicationCodeableConcept': {'text': 'Sinvastatina 40mg'}},
            {'medicationCodeableConcept': {'text': 'AAS 100mg'}},
            {'medicationCodeableConcept': {'text': 'Omeprazol 20mg'}}
        ],
        'vital_signs': [
            {
                'code': {'coding': [{'code': '8480-6'}], 'text': 'PA Sistólica'},
                'valueQuantity': {'value': 165, 'unit': 'mmHg'}
            },
            {
                'code': {'coding': [{'code': '8462-4'}], 'text': 'PA Diastólica'},
                'valueQuantity': {'value': 95, 'unit': 'mmHg'}
            },
            {
                'code': {'coding': [{'code': '8867-4'}], 'text': 'FC'},
                'valueQuantity': {'value': 88, 'unit': 'bpm'}
            },
            {
                'code': {'coding': [{'code': '2708-6'}], 'text': 'SpO2'},
                'valueQuantity': {'value': 92, 'unit': '%'}
            }
        ]
    }
    
    ai_service = AIService()
    summary = ai_service.generate_patient_summary(patient_data)
    
    print(summary)
    print_separator()


def demo_case_4_critical_vitals():
    """Caso 4: Paciente com sinais vitais críticos."""
    print("📋 CASO 4: Paciente com Sinais Vitais Críticos (Requer Atenção Imediata)")
    print_separator()
    
    patient_data = {
        'name': 'Ana Paula Costa',
        'age': 45,
        'gender': 'female',
        'conditions': [
            {
                'code': {'text': 'Asma'},
                'clinicalStatus': {'coding': [{'code': 'active'}]}
            }
        ],
        'medications': [
            {'medicationCodeableConcept': {'text': 'Salbutamol inalatório'}},
            {'medicationCodeableConcept': {'text': 'Budesonida inalatória'}}
        ],
        'vital_signs': [
            {
                'code': {'coding': [{'code': '8310-5'}], 'text': 'Temperatura'},
                'valueQuantity': {'value': 38.9, 'unit': '°C'}
            },
            {
                'code': {'coding': [{'code': '9279-1'}], 'text': 'FR'},
                'valueQuantity': {'value': 28, 'unit': 'irpm'}
            },
            {
                'code': {'coding': [{'code': '2708-6'}], 'text': 'SpO2'},
                'valueQuantity': {'value': 89, 'unit': '%'}
            },
            {
                'code': {'coding': [{'code': '8867-4'}], 'text': 'FC'},
                'valueQuantity': {'value': 115, 'unit': 'bpm'}
            }
        ]
    }
    
    ai_service = AIService()
    summary = ai_service.generate_patient_summary(patient_data)
    
    print(summary)
    print_separator()


def main():
    """Executa todas as demonstrações."""
    print("\n" + "🎯" * 40)
    print("DEMONSTRAÇÃO: MELHORIAS NOS RESUMOS CLÍNICOS DA IA")
    print("Objetivo: Ajudar profissionais a tomar decisões assertivas")
    print("🎯" * 40)
    
    demo_case_1_simple_patient()
    input("Pressione ENTER para ver o próximo caso...")
    
    demo_case_2_diabetic_hypertensive()
    input("Pressione ENTER para ver o próximo caso...")
    
    demo_case_3_complex_elderly()
    input("Pressione ENTER para ver o próximo caso...")
    
    demo_case_4_critical_vitals()
    
    print("\n" + "✅" * 40)
    print("MELHORIAS IMPLEMENTADAS:")
    print("✅" * 40)
    print("""
1. ✅ Resumo Executivo: Apresenta complexidade clínica logo no início
2. ✅ Análise de Sinais Vitais: Interpretação com faixas de referência
3. ✅ Alertas Clínicos: Destaque visual para situações críticas
4. ✅ Recomendações Baseadas em Evidências: Guidelines específicos
5. ✅ Detecção de Comorbidades: Alertas para múltiplas condições
6. ✅ Identificação de Polifarmácia: Alerta ≥5 medicamentos
7. ✅ Rastreamento Preventivo: Recomendações por idade/gênero
8. ✅ Dados Faltantes: Identifica informações críticas ausentes
9. ✅ Estrutura Organizada: Seções claras com emojis visuais
10. ✅ Linguagem Técnica: Apropriada para profissionais de saúde

🎯 RESULTADO: Resumos fidedignos que auxiliam tomada de decisão assertiva!
    """)


if __name__ == '__main__':
    main()
