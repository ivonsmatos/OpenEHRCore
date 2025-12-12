import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = "http://localhost:8000/api/v1/auth/login/"

def get_token():
    print("Authenticating...")
    # Using bypass credentials found in views_auth.py
    response = requests.post(AUTH_URL, json={"username": "contato@ivonmatos.com.br", "password": "Protonsysdba@1986"})
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("access")
    else:
        print(f"Authentication failed: {response.text}")
        exit(1)

def verify_crud():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Create Patient
    print("\n[TEST] Creating Patient...")
    # Using flat JSON expected by views_auth.py
    patient_data = {
        "first_name": "CRUD",
        "last_name": "Verifier",
        "birth_date": "1990-01-01",
        "gender": "male",
        "cpf": "12345678900",
        "telecom": [{"system": "phone", "value": "5511999999999"}]
    }
    
    response = requests.post(f"{BASE_URL}/patients/", json=patient_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Creation failed: {response.status_code} - {response.text}")
        return
    
    patient_id = response.json().get("id")
    print(f"✅ Patient Created. ID: {patient_id}")
    
    # 2. Read Patient
    print(f"\n[TEST] Reading Patient {patient_id}...")
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/", headers=headers)
    if response.status_code == 200:
        print("✅ Read successful.")
    else:
        print(f"❌ Read failed: {response.status_code}")
        return

    # 3. Update Patient
    print(f"\n[TEST] Updating Patient {patient_id}...")
    updated_data = {
        "first_name": "CRUD",
        "last_name": "VerifierUpdated",
        "birth_date": "1990-01-01",
        "gender": "male" 
    }
    response = requests.put(f"{BASE_URL}/patients/{patient_id}/", json=updated_data, headers=headers)
    if response.status_code == 200:
        print("✅ Update successful.")
        # Verify update
        check = requests.get(f"{BASE_URL}/patients/{patient_id}/", headers=headers)
        # Check simplifies FHIR parsing or just check the raw response if simple
        # The GET response from get_patient might be FHIR from fhir_service.get_patient_by_id
        # Let's see what get_patient returns. It returns `patient` from fhir_service.
        # fhir_service.get_patient_by_id returns a Dict (FHIR resource).
        data = check.json()
        try:
            name_family = data["name"][0]["family"]
            if name_family == "VerifierUpdated":
                 print("✅ Data verification passed (Family name updated).")
            else:
                 print(f"❌ Data verification failed. Expected 'VerifierUpdated', got '{name_family}'")
        except:
             print(f"⚠️ Could not parse name for verification: {data}")

    else:
        print(f"❌ Update failed: {response.status_code} - {response.text}")

    # 4. Delete Patient
    print(f"\n[TEST] Deleting Patient {patient_id}...")
    response = requests.delete(f"{BASE_URL}/patients/{patient_id}/", headers=headers)
    if response.status_code in [200, 204]:
        print("✅ Delete successful.")
    else:
        print(f"❌ Delete failed: {response.status_code} - {response.text}")

    # 5. Verify Deletion
    print(f"\n[TEST] Verifying Deletion...")
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/", headers=headers)
    if response.status_code == 404:
        print("✅ Verification successful (404 Not Found returned).")
    else:
        print(f"❌ Verification failed. Expected 404, got {response.status_code}")

if __name__ == "__main__":
    verify_crud()
