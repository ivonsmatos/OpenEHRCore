
import requests
import json

token = "dev-token-bypass"
base_url = "http://localhost:8000/api/v1/chat"

print("--- Testing Chat API Robustness ---")

# 1. Create Team
print("\n[1] Creating Team 'Equipe UTIs'...")
try:
    payload = {"name": "Equipe UTIs"}
    r = requests.post(f"{base_url}/channels/create/", json=payload, headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(r.text)
except Exception as e:
    print(f"Error: {e}")

# 2. List Channels (Check if Team appears)
print("\n[2] Listing Channels...")
try:
    r = requests.get(f"{base_url}/channels/", headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    print(f"Channels found: {len(data.get('channels', []))}")
    for ch in data.get('channels', []):
        if "Equipe UTIs" in ch['name']:
            print(f" [OK] Found new team: {ch['name']}")
except Exception as e:
    print(f"Error: {e}")

# 3. Send Message with MISSING sender_id (Should NOT 500)
print("\n[3] Sending Anonymous Message (Testing 500 fix)...")
try:
    payload = {
        "channel_id": "general",
        "content": "Message with no sender ID",
        # sender_id MISSING
    }
    r = requests.post(f"{base_url}/send/", json=payload, headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(r.text)
    if r.status_code == 201:
        print(" [OK] Message sent successfully (handled gracefully)")
    else:
        print(" [FAIL] Message failed")
except Exception as e:
    print(f"Error: {e}")
