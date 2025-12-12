import os
import requests
import sys
from decouple import config

# Tentar carregar do .env se possível, mas vamos definir valores hardcoded para teste se falhar
# Assumindo que o usuário está rodando onde o .env está acessível ou as vars estão no ambiente

KEYCLOAK_URL = "http://localhost:8180"
REALM = "master"
CLIENT_ID = "openehrcore"
# Tente pegar do ambiente ou use vazio para ver se falha
CLIENT_SECRET = config('KEYCLOAK_CLIENT_SECRET', default='')

USERNAME = "medico@example.com"
PASSWORD = "senha123!@#"

def debug_auth():
    print(f"--- Debugging Keycloak Auth ---")
    print(f"URL: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {'*' * len(CLIENT_SECRET) if CLIENT_SECRET else 'NOT SET'}")

    # 1. Tentar Login
    print("\n1. Tentando Login...")
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    try:
        response = requests.post(token_url, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': USERNAME,
            'password': PASSWORD,
            'grant_type': 'password',
            'scope': 'openid profile email'
        })
        
        if response.status_code != 200:
            print(f"❌ Login falhou: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        access_token = data.get('access_token')
        print("✅ Login com sucesso!")
        print(f"Token (primeiros 20 chars): {access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Erro na requisição de login: {e}")
        return

    # 2. Tentar Introspecção
    print("\n2. Tentando Introspecção (Backend validation)...")
    introspect_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token/introspect"
    try:
        response = requests.post(introspect_url, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'token': access_token
        })
        
        if response.status_code != 200:
            print(f"❌ Introspecção falhou: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {data}")
        
        if data.get('active') is True:
            print("✅ Token VÁLIDO e ATIVO!")
        else:
            print("❌ Token INVÁLIDO ou INATIVO (active=False)")
            
    except Exception as e:
        print(f"❌ Erro na requisição de introspecção: {e}")

if __name__ == "__main__":
    # Adicionar caminho do backend para o decouple funcionar se tiver .env lá
    sys.path.append(os.path.join(os.getcwd(), 'backend-django'))
    debug_auth()
