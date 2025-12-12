
import requests

def check_id():
    url = "http://localhost:8080/fhir/Composition/10"
    print(f"Checking {url}...")
    resp = requests.get(url)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Document EXISTS.")
        print(resp.text[:200])
    else:
        print("Document NOT FOUND.")

if __name__ == "__main__":
    check_id()
