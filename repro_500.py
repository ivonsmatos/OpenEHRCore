import requests
import sys

try:
    url = "http://localhost:8000/api/v1/patients/patient-1/"
    print(f"Requesting {url}...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
