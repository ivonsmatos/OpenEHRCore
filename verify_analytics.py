
import requests
import json

LOGIN_URL = "http://localhost:8000/api/v1/auth/login/"
ANALYTICS_URL = "http://localhost:8000/api/v1/analytics/dashboard/"

def get_token():
    try:
        resp = requests.post(LOGIN_URL, json={"username": "contato@ivonmatos.com.br", "password": "Protonsysdba@1986"})
        if resp.status_code == 200:
            data = resp.json()
            return data.get('access_token') or data.get('access')
    except Exception as e:
        print(f"Login error: {e}")
    return None

def verify_analytics():
    print("Getting token...")
    token = get_token()
    if not token:
        print("Failed to get token.")
        return

    print(f"Checking {ANALYTICS_URL}...")
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(ANALYTICS_URL, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Analytics Data:")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    verify_analytics()
