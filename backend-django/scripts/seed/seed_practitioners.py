
import os
import django
import logging

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
import sys
sys.path.append(os.getcwd()) # Add current dir
django.setup()

from fhir_api.services.fhir_core import FHIRService

fhir = FHIRService()

PRACTITIONERS = [
    # Médicos
    {
        "name": "Dr. Roberto Silva",
        "gender": "male",
        "role": "Cirurgião Geral",
        "specialty_code": "394609007", # General surgery
        "specialty_display": "General Surgery"
    },
    {
        "name": "Dra. Ana Costa",
        "gender": "female",
        "role": "Cardiologista",
        "specialty_code": "394579002", # Cardiology
        "specialty_display": "Cardiology"
    },
    {
        "name": "Dr. Carlos Santos",
        "gender": "male",
        "role": "Anestesiologista",
        "specialty_code": "394577000", # Anesthetics
        "specialty_display": "Anesthetics"
    },
    # Enfermagem
    {
        "name": "Enf. Mariana Santos",
        "gender": "female",
        "role": "Enfermeira Chefe",
        "specialty_code": "106292003", # Professional nurse
        "specialty_display": "Professional nurse"
    },
    {
        "name": "Enf. Pedro Almeida",
        "gender": "male",
        "role": "Enfermeiro de UTI",
        "specialty_code": "408467006", # Critical care nurse
        "specialty_display": "Critical care nurse"
    },
    # Técnicos e Auxiliares
    {
        "name": "Tec. Julia Oliveira",
        "gender": "female",
        "role": "Técnica de Enfermagem",
        "specialty_code": "159016003", # Nursing assistant
        "specialty_display": "Nursing assistant"
    },
    {
        "name": "Tec. Rafael Souza",
        "gender": "male",
        "role": "Técnico de Raio-X",
        "specialty_code": "159021000", # Radiographer
        "specialty_display": "Radiographer"
    },
    {
        "name": "Aux. João Pereira",
        "gender": "male",
        "role": "Auxiliar Administrativo",
        "specialty_code": "159142007", # Clerk
        "specialty_display": "Clerk"
    },
    {
        "name": "Aux. Maria Lima",
        "gender": "female",
        "role": "Auxiliar de Limpeza",
        "specialty_code": "224571005", # Cleaner
        "specialty_display": "Cleaner"
    }
]

def seed_practitioners():
    print(f"--- Populando {len(PRACTITIONERS)} Profissionais de Saúde ---")
    
    for p_data in PRACTITIONERS:
        try:
            name_parts = p_data["name"].split(" ")
            first_name = name_parts[0] + " " + name_parts[1] if len(name_parts) > 2 else name_parts[0]
            family_name = name_parts[-1]
            
            practitioner = {
                "resourceType": "Practitioner",
                "active": True,
                "name": [{
                    "use": "official",
                    "text": p_data["name"],
                    "family": family_name,
                    "given": first_name.split()
                }],
                "gender": p_data["gender"],
                "qualification": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": p_data["specialty_code"],
                                    "display": p_data["specialty_display"]
                                }
                            ],
                            "text": p_data["role"]
                        }
                    }
                ]
            }
            
            # Check duplication (mock check by name roughly?)
            # For simplicity, just create.
            
            result = fhir.create_resource("Practitioner", practitioner)
            print(f" [OK] Criado: {p_data['name']} (ID: {result['id']})")
            
        except Exception as e:
            print(f" [ERR] Falha ao criar {p_data['name']}: {e}")

if __name__ == '__main__':
    seed_practitioners()
