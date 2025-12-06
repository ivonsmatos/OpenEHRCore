
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Use the dev token bypass logic if available, or just try without and see
# We can simulate the dev-token-bypass token defined in Authentication class
TOKEN = "dev-token-bypass"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def check_endpoint(name, url):
    print(f"\n--- Checking {name} [{url}] ---")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"Status: {response.status_code}")
        try:
            content = response.json()
            print("Body (JSON):")
            print(json.dumps(content, indent=2, ensure_ascii=False))
        except:
            print("Body (Text/HTML) - Saving to last_error.html")
            with open("last_error.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(response.text[:200]) # First 200 chars
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    check_endpoint("Patients List", f"{BASE_URL}/patients/?page=1")
    check_endpoint("Documents List", f"{BASE_URL}/documents/")
    check_endpoint("KPI Metrics", f"{BASE_URL}/analytics/kpi/")
    check_endpoint("Clinical Metrics", f"{BASE_URL}/analytics/clinical/")
    check_endpoint("Survey Metrics", f"{BASE_URL}/analytics/survey/")
