
import requests
import json
import time

LOGIN_URL = "http://localhost:8000/api/v1/auth/login/"
DOCS_URL = "http://localhost:8000/api/v1/documents/"

def get_token():
    resp = requests.post(LOGIN_URL, json={"username": "contato@ivonmatos.com.br", "password": "Protonsysdba@1986"})
    if resp.status_code == 200:
        data = resp.json()
        return data.get('access_token') or data.get('access')
    return None

def create_and_verify():
    token = get_token()
    if not token:
        print("Auth failed")
        return

    headers = {'Authorization': f'Bearer {token}'}

    # 1. Create Document
    print("Creating document...")
    payload = {
        "title": "Script Test Generation",
        "doc_type": "evolucao",
        "patient_id": "patient-1", # Must exist
        "practitioner_id": "practitioner-1", # Must exist
        "text_content": "Automated test content."
    }
    
    resp = requests.post(DOCS_URL, json=payload, headers=headers)
    print(f"Create Status: {resp.status_code}")
    print(f"Create Body: {resp.text}")
    
    if resp.status_code not in [200, 201]:
        print("Creation failed!")
        return

    # 2. Check List immediately
    print("Checking list...")
    # time.sleep(1) # Optional delay check
    resp = requests.get(DOCS_URL, headers=headers)
    data = resp.json()
    print(f"List count: {len(data)}")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    create_and_verify()
