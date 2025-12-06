
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = "http://localhost:8000/api/v1/auth/login/"
USERNAME = "dev"
PASSWORD = "dev"

def get_token():
    try:
        response = requests.post(AUTH_URL, json={'username': USERNAME, 'password': PASSWORD})
        response.raise_for_status()
        return response.json()['token']
    except Exception as e:
        print(f"❌ Failed to login: {e}")
        return None

def test_ai_summary(token, patient_id):
    print(f"\n🔍 Testing AI Summary for Patient {patient_id}...")
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(f"{BASE_URL}/ai/summary/{patient_id}/", headers=headers)
        if response.status_code == 200:
            print("✅ AI Summary endpoint reachable (200 OK)")
            data = response.json()
            if 'summary' in data:
                print(f"✅ Summary generated: {data['summary'][:100]}...")
            else:
                print("❌ 'summary' field missing in response")
        else:
            print(f"❌ Failed to get summary: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception calling summary: {e}")

def test_ai_interactions(token, patient_id):
    print(f"\n🔍 Testing AI Interactions (Mock)...")
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        "new_medication": "Warfarin",
        "patient_id": patient_id
    }
    
    # We expect alerts if patient has Aspirin, but we don't know patient state.
    # So we mainly test endpoint reachability and response structure.
    try:
        response = requests.post(f"{BASE_URL}/ai/interactions/", json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ AI Interactions endpoint reachable (200 OK)")
            data = response.json()
            if 'alerts' in data:
                print(f"✅ Alerts returned: {len(data['alerts'])}")
                print(f"   Alerts: {json.dumps(data['alerts'], indent=2)}")
            else:
                print("❌ 'alerts' field missing in response")
        else:
            print(f"❌ Failed to check interactions: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception calling interactions: {e}")

if __name__ == "__main__":
    print("🚀 Starting AI Verification...")
    token = get_token()
    if token:
        # Assuming we have a patient from previous tests, or creating one?
        # Let's try to export/list patients to find one ID, or use a hardcoded one if we created previously.
        # Ideally we should fetch a patient list first.
        
        # List patients to get an ID
        headers = {'Authorization': f'Bearer {token}'}
        try:
            resp = requests.get(f"{BASE_URL}/patients/", headers=headers)
            if resp.status_code == 200 and len(resp.json()) > 0:
                patient_id = resp.json()[0]['id']
                test_ai_summary(token, patient_id)
                test_ai_interactions(token, patient_id)
            else:
                print("⚠️ No patients found to test AI summary.")
        except Exception as e:
            print(f"❌ Failed to list patients: {e}")

    print("\n🏁 AI Verification Finished.")
