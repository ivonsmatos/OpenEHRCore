
import requests
import json

# HAPI FHIR URL (Default for local setup)
FHIR_URL = "http://localhost:8080/fhir"

def create_resource_if_not_exists(resource_type, resource_id, resource_body):
    url = f"{FHIR_URL}/{resource_type}/{resource_id}"
    print(f"Checking {url}...")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ {resource_type}/{resource_id} already exists.")
            return

        print(f"Creating {resource_type}/{resource_id}...")
        # Use PUT to define the ID explicitly
        response = requests.put(url, json=resource_body)
        
        if response.status_code in [200, 201]:
             print(f"✅ {resource_type}/{resource_id} created successfully.")
        else:
             print(f"❌ Failed to create {resource_type}/{resource_id}: {response.status_code} {response.text}")
             
    except Exception as e:
        print(f"❌ Error connecting to FHIR server: {e}")

# 1. Ensure Practitioner (Dr. Mock)
practitioner_data = {
    "resourceType": "Practitioner",
    "id": "practitioner-1",
    "name": [
        {
            "family": "Matos",
            "given": ["Ivon", "Dr."]
        }
    ],
    "telecom": [
        {
            "system": "email",
            "value": "dr.ivon@example.com"
        }
    ]
}

# 2. Ensure Patient (patient-1) - Just in case
patient_data = {
    "resourceType": "Patient",
    "id": "patient-1",
    "name": [
        {
            "family": "Silva",
            "given": ["Joao", "Teste"]
        }
    ],
    "gender": "male",
    "birthDate": "1980-01-01"
}

if __name__ == "__main__":
    print("--- Ensuring FHIR Resources ---")
    create_resource_if_not_exists("Practitioner", "practitioner-1", practitioner_data)
    create_resource_if_not_exists("Patient", "patient-1", patient_data)
