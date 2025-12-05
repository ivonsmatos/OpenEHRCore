
import requests
import json

LOGIN_URL = "http://localhost:8000/api/v1/auth/login/"
DOCS_URL = "http://localhost:8000/api/v1/documents/"

def get_token():
    creds = [
        ("admin", "admin"),
        ("contato@ivonmatos.com.br", "Protonsysdba@1986"),
        ("medico@example.com", "senha123!@#"),
        ("paciente@teste.com", "senha123")
    ]
    
    for username, password in creds:
        print(f"Trying login with {username}...")
        try:
            resp = requests.post(LOGIN_URL, json={"username": username, "password": password})
            if resp.status_code == 200:
                print("Recall received token.")
                data = resp.json()
                return data.get('access_token') or data.get('access')
            else:
                print(f"Failed: {resp.status_code}")
        except Exception as e:
            print(f"Connection error: {e}")
    return None

def check_list():
    token = get_token()
    if not token:
        print("Could not log in to check list.")
        return

    print(f"Checking {DOCS_URL}...")
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(DOCS_URL, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Data received (List len={len(data)}):")
            print(json.dumps(data, indent=2))
        else:
            print("Error body:")
            print(resp.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_list()
