import requests
import time

KEYCLOAK_URL = "http://localhost:8180"
ADMIN_USER = "admin"
ADMIN_PASS = "admin_password_123"
REALM = "master"

def get_admin_token():
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
        "grant_type": "password",
        "client_id": "admin-cli"
    }
    print(f"Getting admin token from {url}...")
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print(f"Failed to get token: {resp.status_code} {resp.text}")
        resp.raise_for_status()
    return resp.json()["access_token"]

def create_client(token):
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Check if exists
    search = requests.get(url, headers=headers, params={"clientId": "openehrcore"})
    if search.json():
        print("Client 'openehrcore' already exists")
        return

    client_data = {
        "clientId": "openehrcore",
        "enabled": True,
        "publicClient": True,
        "directAccessGrantsEnabled": True,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "serviceAccountsEnabled": False,
        "redirectUris": ["http://localhost:5173/*"],
        "webOrigins": ["http://localhost:5173", "+"]
    }

    resp = requests.post(url, json=client_data, headers=headers)
    if resp.status_code == 201:
        print("Client 'openehrcore' created successfully")
    else:
        print(f"Failed to create client: {resp.status_code} {resp.text}")

def create_user(token):
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Check if exists
    search = requests.get(url, headers=headers, params={"username": "medico"})
    if search.json():
        print("User 'medico' already exists")
        return

    user_data = {
        "username": "medico",
        "email": "medico@example.com",
        "enabled": True,
        "firstName": "João",
        "lastName": "Silva",
        "credentials": [{
            "type": "password",
            "value": "senha123!@#",
            "temporary": False
        }]
    }

    resp = requests.post(url, json=user_data, headers=headers)
    if resp.status_code == 201:
        print("User 'medico' created successfully")
    else:
        print(f"Failed to create user: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    print("Waiting for Keycloak to be ready...")
    # Simple retry logic
    for i in range(10):
        try:
            requests.get(f"{KEYCLOAK_URL}/realms/master")
            break
        except:
            time.sleep(2)
            print(".", end="", flush=True)
    print("\nStarting setup...")
    
    try:
        token = get_admin_token()
        create_client(token)
        create_user(token)
        print("Keycloak setup completed!")
    except Exception as e:
        print(f"Error during setup: {e}")
