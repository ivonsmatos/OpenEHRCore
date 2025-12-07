#!/usr/bin/env python
"""
FHIR Compliance Test Suite
Tests all FHIR resources for R4 compliance
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
FHIR_BASE = "http://localhost:8065/fhir"

# Test credentials
USERNAME = "dev"
PASSWORD = "dev"

def get_token():
    """Authenticate and get token"""
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        return response.json()['access']
    raise Exception(f"Login failed: {response.text}")

def test_patient_fhir_compliance(token):
    """Test Patient resource FHIR R4 compliance"""
    print("\n=== Testing Patient FHIR Compliance ===")
    
    # Create patient with all FHIR required fields
    patient_data = {
        "name": "João Silva Teste",
        "birthDate": "1990-05-15",
        "gender": "male",
        "cpf": "123.456.789-00",
        "phone": "(11) 98765-4321",
        "email": "joao.teste@example.com",
        "address": "Rua Teste, 123, São Paulo, SP"
    }
    
    response = requests.post(
        f"{BASE_URL}/patients/",
        json=patient_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code in [200, 201]:
        patient = response.json()
        patient_id = patient.get('id')
        print(f"✅ Patient created: {patient_id}")
        
        # Verify FHIR structure directly from HAPI
        fhir_response = requests.get(f"{FHIR_BASE}/Patient/{patient_id}")
        if fhir_response.status_code == 200:
            fhir_patient = fhir_response.json()
            
            # Check required FHIR fields
            checks = {
                "resourceType": fhir_patient.get('resourceType') == 'Patient',
                "id": fhir_patient.get('id') is not None,
                "name": len(fhir_patient.get('name', [])) > 0,
                "gender": fhir_patient.get('gender') in ['male', 'female', 'other', 'unknown'],
                "birthDate": fhir_patient.get('birthDate') is not None,
            }
            
            for field, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {field}: {passed}")
            
            return patient_id
    else:
        print(f"❌ Failed to create patient: {response.text}")
        return None

def test_practitioner_fhir_compliance(token):
    """Test Practitioner resource FHIR R4 compliance"""
    print("\n=== Testing Practitioner FHIR Compliance ===")
    
    # Create practitioner directly in FHIR
    practitioner_fhir = {
        "resourceType": "Practitioner",
        "active": True,
        "name": [{
            "use": "official",
            "family": "Santos",
            "given": ["Maria", "da", "Silva"],
            "prefix": ["Dra."]
        }],
        "telecom": [
            {
                "system": "phone",
                "value": "(11) 3456-7890",
                "use": "work"
            },
            {
                "system": "email",
                "value": "maria.santos@hospital.com",
                "use": "work"
            }
        ],
        "gender": "female",
        "birthDate": "1985-03-20",
        "qualification": [{
            "code": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                    "code": "MD",
                    "display": "Doctor of Medicine"
                }],
                "text": "Médica"
            }
        }]
    }
    
    response = requests.post(
        f"{FHIR_BASE}/Practitioner",
        json=practitioner_fhir,
        headers={"Content-Type": "application/fhir+json"}
    )
    
    if response.status_code in [200, 201]:
        practitioner = response.json()
        practitioner_id = practitioner.get('id')
        print(f"✅ Practitioner created: {practitioner_id}")
        
        # Verify structure
        checks = {
            "resourceType": practitioner.get('resourceType') == 'Practitioner',
            "id": practitioner.get('id') is not None,
            "name": len(practitioner.get('name', [])) > 0,
            "active": practitioner.get('active') is not None,
        }
        
        for field, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {field}: {passed}")
        
        return practitioner_id
    else:
        print(f"❌ Failed to create practitioner: {response.text}")
        return None

def test_observation_fhir_compliance(token, patient_id):
    """Test Observation (Vital Signs) FHIR R4 compliance"""
    print("\n=== Testing Observation FHIR Compliance ===")
    
    # Create vital signs observation
    observation_data = {
        "patient_id": patient_id,
        "code": "85354-9",  # Blood pressure LOINC code
        "value": "120",
        "unit": "mmHg",
        "systolic": 120,
        "diastolic": 80
    }
    
    response = requests.post(
        f"{BASE_URL}/clinical/vital-signs/",
        json=observation_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code in [200, 201]:
        obs = response.json()
        obs_id = obs.get('id')
        print(f"✅ Observation created: {obs_id}")
        
        # Verify FHIR structure
        fhir_response = requests.get(f"{FHIR_BASE}/Observation/{obs_id}")
        if fhir_response.status_code == 200:
            fhir_obs = fhir_response.json()
            
            checks = {
                "resourceType": fhir_obs.get('resourceType') == 'Observation',
                "status": fhir_obs.get('status') in ['registered', 'preliminary', 'final', 'amended'],
                "code": fhir_obs.get('code') is not None,
                "subject": fhir_obs.get('subject') is not None,
                "effectiveDateTime": fhir_obs.get('effectiveDateTime') is not None,
            }
            
            for field, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {field}: {passed}")
    else:
        print(f"❌ Failed to create observation: {response.text}")

def test_encounter_fhir_compliance(token, patient_id):
    """Test Encounter (IPD) FHIR R4 compliance"""
    print("\n=== Testing Encounter FHIR Compliance ===")
    
    # Get a free bed
    response = requests.get(
        f"{BASE_URL}/ipd/locations/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        locations = response.json()
        
        # Find a free bed
        def find_free_bed(nodes):
            for node in nodes:
                if node.get('status_code') == 'U':
                    is_bed = (node.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' 
                             or node.get('name', '').startswith('Leito'))
                    if is_bed:
                        return node.get('id')
                if node.get('children'):
                    bed_id = find_free_bed(node['children'])
                    if bed_id:
                        return bed_id
            return None
        
        bed_id = find_free_bed(locations)
        
        if bed_id:
            # Admit patient
            admit_data = {
                "patient_id": patient_id,
                "location_id": bed_id,
                "reason": "Teste de conformidade FHIR"
            }
            
            response = requests.post(
                f"{BASE_URL}/ipd/admit/",
                json=admit_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code in [200, 201]:
                encounter = response.json()
                encounter_id = encounter.get('encounter_id')
                print(f"✅ Encounter created: {encounter_id}")
                
                # Verify FHIR structure
                fhir_response = requests.get(f"{FHIR_BASE}/Encounter/{encounter_id}")
                if fhir_response.status_code == 200:
                    fhir_enc = fhir_response.json()
                    
                    checks = {
                        "resourceType": fhir_enc.get('resourceType') == 'Encounter',
                        "status": fhir_enc.get('status') in ['planned', 'arrived', 'in-progress', 'finished'],
                        "class": fhir_enc.get('class') is not None,
                        "subject": fhir_enc.get('subject') is not None,
                        "period": fhir_enc.get('period') is not None,
                        "location": len(fhir_enc.get('location', [])) > 0,
                    }
                    
                    for field, passed in checks.items():
                        status = "✅" if passed else "❌"
                        print(f"  {status} {field}: {passed}")
                    
                    return encounter_id
            else:
                print(f"❌ Failed to create encounter: {response.text}")
        else:
            print("⚠️  No free bed available for encounter test")
    
    return None

def test_composition_fhir_compliance(token, patient_id):
    """Test Composition (Clinical Document) FHIR R4 compliance"""
    print("\n=== Testing Composition FHIR Compliance ===")
    
    doc_data = {
        "patient_id": patient_id,
        "title": "Anamnese Teste FHIR",
        "type": "anamnese",
        "content": "Paciente relata cefaleia há 3 dias. Sem febre. Teste de conformidade FHIR R4."
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/create/",
        json=doc_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code in [200, 201]:
        doc = response.json()
        doc_id = doc.get('id')
        print(f"✅ Composition created: {doc_id}")
        
        # Verify FHIR structure
        fhir_response = requests.get(f"{FHIR_BASE}/Composition/{doc_id}")
        if fhir_response.status_code == 200:
            fhir_comp = fhir_response.json()
            
            checks = {
                "resourceType": fhir_comp.get('resourceType') == 'Composition',
                "status": fhir_comp.get('status') in ['preliminary', 'final', 'amended'],
                "type": fhir_comp.get('type') is not None,
                "subject": fhir_comp.get('subject') is not None,
                "date": fhir_comp.get('date') is not None,
                "author": len(fhir_comp.get('author', [])) > 0,
                "title": fhir_comp.get('title') is not None,
            }
            
            for field, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {field}: {passed}")
    else:
        print(f"❌ Failed to create composition: {response.text}")

def main():
    print("=" * 60)
    print("FHIR R4 COMPLIANCE TEST SUITE")
    print("=" * 60)
    
    try:
        # Get authentication token
        print("\n🔐 Authenticating...")
        token = get_token()
        print("✅ Authentication successful")
        
        # Test Patient
        patient_id = test_patient_fhir_compliance(token)
        
        # Test Practitioner
        practitioner_id = test_practitioner_fhir_compliance(token)
        
        if patient_id:
            # Test Observation
            test_observation_fhir_compliance(token, patient_id)
            
            # Test Encounter
            encounter_id = test_encounter_fhir_compliance(token, patient_id)
            
            # Test Composition
            test_composition_fhir_compliance(token, patient_id)
        
        print("\n" + "=" * 60)
        print("✅ FHIR COMPLIANCE TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
