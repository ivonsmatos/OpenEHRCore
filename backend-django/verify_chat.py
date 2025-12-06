
import requests
import json

token = "dev-token-bypass"
base_url = "http://localhost:8000/api/v1/chat"

print("--- Testing Chat API ---")

# 1. List Channels
print("\n[1] Listing Channels...")
try:
    r = requests.get(f"{base_url}/channels/", headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Channels found: {len(data['channels'])}")
        print(f"Users found: {len(data['users'])}")
        user_id = data['users'][0]['id'] if data['users'] else "123"
    else:
        print(r.text)
        user_id = "123"
except Exception as e:
    print(f"Error: {e}")
    user_id = "123"

# 2. Send Message to General
print("\n[2] Sending Message to #general...")
try:
    payload = {
        "channel_id": "general",
        "content": "Hello World from Test Script",
        "sender_id": user_id
    }
    r = requests.post(f"{base_url}/send/", json=payload, headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(r.text)
except Exception as e:
    print(f"Error: {e}")

# 3. List Messages from General
print("\n[3] Listing Messages from #general...")
try:
    r = requests.get(f"{base_url}/messages/?channel_id=general", headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        msgs = r.json()
        print(f"Messages found: {len(msgs)}")
        if msgs:
            print(f"Last message: {msgs[-1]['content']}")
    else:
        print(r.text)
except Exception as e:
    print(f"Error: {e}")
