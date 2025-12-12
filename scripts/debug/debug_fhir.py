from fhirclient import client
import requests
import json

# Configuração igual ao settings.py
FHIR_SERVER_URL = 'http://localhost:8080/fhir'

def debug_fhir():
    print(f"--- Debugging FHIR Connection ---")
    print(f"URL: {FHIR_SERVER_URL}")

    # 1. Teste simples com requests
    print("\n1. Testando conexão HTTP direta...")
    try:
        # Tentar metadata
        url = f"{FHIR_SERVER_URL}/metadata"
        print(f"GET {url}")
        response = requests.get(url, headers={'Accept': 'application/json'})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Conexão HTTP OK!")
        else:
            print(f"❌ Falha HTTP: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

    # 2. Teste com fhirclient
    print("\n2. Testando com fhirclient...")
    try:
        settings = {
            'app_id': 'debug_app',
            'api_base': FHIR_SERVER_URL
        }
        smart = client.FHIRClient(settings=settings)
        
        print("Tentando ler CapabilityStatement (prepare)...")
        # O prepare() geralmente busca o metadata
        smart.prepare()
        print("✅ fhirclient.prepare() OK!")
        
        if smart.server.auth is not None:
             print(f"Auth config detectada: {smart.server.auth.as_json()}")
        
    except Exception as e:
        print(f"❌ Erro fhirclient: {e}")

if __name__ == "__main__":
    debug_fhir()
