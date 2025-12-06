import requests
import json

token = "dev-token-bypass"
url = "http://localhost:8000/api/v1/visitors/create/"
patient_id = "3045" # Using the ID from the user report/screenshot logic roughly

payload = {
    "name": "Debug Visitor",
    "phone": "12345678",
    "relationship": "Visitante",
    "patient_id": patient_id
}

print(f"Sending POST to {url} with payload: {json.dumps(payload)}")
try:
    r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
