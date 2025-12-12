
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer dev-token-bypass",
    "Accept": "application/json"
}

try:
    print(f"Checking Admissions Endpoint...")
    resp = requests.get(f"{BASE_URL}/analytics/admissions/", headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        print(f"SUCCESS: Returned {len(data)} admissions.")
        if len(data) > 0:
            print("Sample:", data[0])
    else:
        print(f"FAIL: {resp.status_code} {resp.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")
