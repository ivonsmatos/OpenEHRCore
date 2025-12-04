import requests
import jwt
import json

API_URL = "http://localhost:8000/api/v1"
USERNAME = "medico@example.com"
PASSWORD = "senha123!@#"

def check_roles():
    print("🔑 Autenticando...")
    response = requests.post(f"{API_URL}/auth/login/", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Falha no login: {response.text}")
        return

    token = response.json()["access_token"]
    print("✅ Token obtido.")
    
    # Decodificar sem verificar assinatura (apenas para ver o payload)
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    print("\n--- Payload do Token ---")
    print(json.dumps(decoded, indent=2))
    
    realm_roles = decoded.get('realm_access', {}).get('roles', [])
    resource_access = decoded.get('resource_access', {})
    
    print(f"\nRealm Roles: {realm_roles}")
    print(f"Resource Access: {resource_access}")

if __name__ == "__main__":
    check_roles()
