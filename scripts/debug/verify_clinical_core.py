
import requests
import json
import datetime

LOGIN_URL = "http://localhost:8000/api/v1/auth/login/"
BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    try:
        resp = requests.post(LOGIN_URL, json={"username": "contato@ivonmatos.com.br", "password": "Protonsysdba@1986"})
        if resp.status_code == 200:
            data = resp.json()
            return data.get('access_token') or data.get('access')
    except Exception as e:
        print(f"Login error: {e}")
    return None

def verify_clinical():
    print("Getting token...")
    token = get_token()
    if not token:
        print("Failed to get token.")
        return

    headers = {'Authorization': f'Bearer {token}'}
    patient_id = "patient-1" # Assuming exists
    
    # 1. Create Immunization
    print("\n--- Creating Immunization ---")
    payload_imm = {
        "patient_id": patient_id,
        "vaccine_code": "03",
        "vaccine_name": "MMR",
        "date": "2023-05-20",
        "lot_number": "MMR123"
    }
    resp = requests.post(f"{BASE_URL}/immunizations/", json=payload_imm, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 201:
        print("Created successfully.")
    else:
        print(f"Error: {resp.text}")

    # 2. List Immunizations
    print("\n--- Listing Immunizations ---")
    resp = requests.get(f"{BASE_URL}/patients/{patient_id}/immunizations/", headers=headers)
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=2))
        
    # 3. Create Diagnostic Report
    print("\n--- Creating Diagnostic Report ---")
    payload_rep = {
        "patient_id": patient_id,
        "code": "58410-2",
        "name": "Complete blood count",
        "date": "2023-06-01",
        "conclusion": "Normal limits."
    }
    resp = requests.post(f"{BASE_URL}/diagnostic-reports/", json=payload_rep, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 201:
        print("Created successfully.")

    # 4. List Diagnostic Reports
    print("\n--- Listing Diagnostic Reports ---")
    resp = requests.get(f"{BASE_URL}/patients/{patient_id}/diagnostic-reports/", headers=headers)
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    verify_clinical()
