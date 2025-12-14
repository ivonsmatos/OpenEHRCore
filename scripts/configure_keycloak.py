import requests
import time

KEYCLOAK_URL = "http://localhost:8180"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
REALM_NAME = "openehrcore"
CLIENT_ID = "openehrcore"

def get_admin_token():
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
        "grant_type": "password",
        "client_id": "admin-cli"
    }
    try:
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            return resp.json()["access_token"]
        else:
            print(f"❌ Falha ao obter token admin: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def create_realm(token):
    url = f"{KEYCLOAK_URL}/admin/realms"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "id": REALM_NAME,
        "realm": REALM_NAME,
        "enabled": True
    }
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        print(f"✅ Realm '{REALM_NAME}' criado.")
    elif resp.status_code == 409:
        print(f"⚠️ Realm '{REALM_NAME}' já existe.")
    else:
        print(f"❌ Falha ao criar realm: {resp.text}")

def create_client(token):
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "clientId": CLIENT_ID,
        "enabled": True,
        "publicClient": True,
        "directAccessGrantsEnabled": True,
        "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/*"],
        "webOrigins": ["+"]
    }
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        print(f"✅ Client '{CLIENT_ID}' criado.")
    elif resp.status_code == 409:
        print(f"⚠️ Client '{CLIENT_ID}' já existe.")
    else:
        print(f"❌ Falha ao criar client: {resp.text}")

def create_user(token):
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Criar usuário
    user_data = {
        "username": "medico@example.com",
        "email": "medico@example.com",
        "firstName": "Medico",
        "lastName": "Exemplo",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": "senha123!@#",
                "temporary": False
            }
        ]
    }
    resp = requests.post(url, json=user_data, headers=headers)
    if resp.status_code == 201:
        print("✅ Usuário 'medico@example.com' criado.")
    elif resp.status_code == 409:
        print("⚠️ Usuário 'medico@example.com' já existe.")
    else:
        print(f"❌ Falha ao criar usuário: {resp.text}")

def wait_for_keycloak():
    print("⏳ Aguardando Keycloak iniciar...")
    for i in range(30):
        try:
            resp = requests.get(f"{KEYCLOAK_URL}/health/ready") # Endpoint genérico ou apenas root
            if resp.status_code < 500: # Se responder algo, tá vivo
                print("✅ Keycloak acessível.")
                return True
        except:
            pass
        time.sleep(2)
        print(".", end="", flush=True)
    print("\n❌ Timeout aguardando Keycloak.")
    return False

if __name__ == "__main__":
    if wait_for_keycloak():
        # Dar um tempinho extra pro boot completo
        time.sleep(5)
        token = get_admin_token()
        if token:
            create_realm(token)
            create_client(token)
            create_user(token)
            print("\n✨ Configuração do Keycloak concluída!")
