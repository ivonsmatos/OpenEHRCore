
import requests

BACKEND_URL = "http://localhost:8000/api/v1/patients/"
FHIR_URL = "http://localhost:8080/fhir/metadata"

def check_service(name, url):
    print(f"Checking {name} at {url}...")
    try:
        # User auth might be needed for backend, but let's see if it connects at all
        response = requests.get(url, timeout=5)
        print(f"✅ {name} responded with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ {name} is unreachable: {e}")

if __name__ == "__main__":
    check_service("Django Backend", "http://localhost:8000/admin/login/") # Public page
    check_service("HAPI FHIR", FHIR_URL)
