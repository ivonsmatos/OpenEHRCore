"""
Script para adicionar CPF a pacientes que não possuem.
Gera CPFs válidos fictícios para pacientes existentes no sistema FHIR.
"""

import requests
import random
from typing import List, Dict

FHIR_URL = "http://localhost:8080/fhir"


def generate_valid_cpf() -> str:
    """
    Gera um CPF válido com dígitos verificadores corretos.
    ATENÇÃO: Apenas para uso em ambientes de desenvolvimento/testes.
    """
    def calculate_digit(cpf_partial: List[int], weights: List[int]) -> int:
        total = sum(d * w for d, w in zip(cpf_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    # Gerar 9 primeiros dígitos aleatórios
    cpf_digits = [random.randint(0, 9) for _ in range(9)]
    
    # Calcular primeiro dígito verificador
    weights_1 = list(range(10, 1, -1))
    digit_1 = calculate_digit(cpf_digits, weights_1)
    cpf_digits.append(digit_1)
    
    # Calcular segundo dígito verificador
    weights_2 = list(range(11, 1, -1))
    digit_2 = calculate_digit(cpf_digits, weights_2)
    cpf_digits.append(digit_2)
    
    # Converter para string
    cpf_str = ''.join(map(str, cpf_digits))
    return cpf_str


def get_all_patients() -> List[Dict]:
    """Busca todos os pacientes do servidor FHIR."""
    try:
        response = requests.get(f"{FHIR_URL}/Patient?_count=1000")
        response.raise_for_status()
        data = response.json()
        return data.get('entry', [])
    except Exception as e:
        print(f"Erro ao buscar pacientes: {e}")
        return []


def patient_has_cpf(patient: Dict) -> bool:
    """Verifica se o paciente já possui CPF cadastrado."""
    resource = patient.get('resource', {})
    identifiers = resource.get('identifier', [])
    
    for identifier in identifiers:
        id_type = identifier.get('type', {})
        if id_type.get('text') == 'CPF':
            return True
    return False


def add_cpf_to_patient(patient_id: str, cpf: str) -> bool:
    """Adiciona CPF a um paciente existente."""
    try:
        # Buscar paciente atual
        response = requests.get(f"{FHIR_URL}/Patient/{patient_id}")
        response.raise_for_status()
        patient = response.json()
        
        # Adicionar CPF aos identifiers
        if 'identifier' not in patient:
            patient['identifier'] = []
        
        patient['identifier'].append({
            "type": {
                "text": "CPF"
            },
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "value": cpf
        })
        
        # Atualizar paciente
        response = requests.put(f"{FHIR_URL}/Patient/{patient_id}", json=patient)
        response.raise_for_status()
        
        return True
    except Exception as e:
        print(f"Erro ao adicionar CPF ao paciente {patient_id}: {e}")
        return False


def main():
    """Função principal do script."""
    print("🔍 Buscando pacientes sem CPF...")
    
    patients = get_all_patients()
    if not patients:
        print("❌ Nenhum paciente encontrado ou erro ao buscar pacientes.")
        return
    
    print(f"✅ Total de pacientes encontrados: {len(patients)}")
    
    # Filtrar pacientes sem CPF
    patients_without_cpf = [p for p in patients if not patient_has_cpf(p)]
    
    if not patients_without_cpf:
        print("✅ Todos os pacientes já possuem CPF cadastrado!")
        return
    
    print(f"📋 Pacientes sem CPF: {len(patients_without_cpf)}")
    print()
    
    # Adicionar CPF a cada paciente
    cpfs_used = set()
    success_count = 0
    
    for entry in patients_without_cpf:
        patient = entry.get('resource', {})
        patient_id = patient.get('id')
        patient_name = patient.get('name', [{}])[0]
        name_str = f"{' '.join(patient_name.get('given', []))} {patient_name.get('family', '')}"
        
        # Gerar CPF único
        while True:
            cpf = generate_valid_cpf()
            if cpf not in cpfs_used:
                cpfs_used.add(cpf)
                break
        
        print(f"📝 Adicionando CPF {cpf} ao paciente: {name_str} (ID: {patient_id})")
        
        if add_cpf_to_patient(patient_id, cpf):
            success_count += 1
            print(f"   ✅ CPF adicionado com sucesso!")
        else:
            print(f"   ❌ Falha ao adicionar CPF")
        print()
    
    print("=" * 50)
    print(f"✅ Processo concluído!")
    print(f"   Total processado: {len(patients_without_cpf)}")
    print(f"   Sucesso: {success_count}")
    print(f"   Falhas: {len(patients_without_cpf) - success_count}")


if __name__ == "__main__":
    main()
