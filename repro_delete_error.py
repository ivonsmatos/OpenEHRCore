
import requests

# Backend URL
BASE_URL = "http://localhost:8000/api/v1/documents"
# Admin credentials (adjust if needed, or use the token mechanism from verify_crud.py if I had it handy, 
# but for a 500 error reproduction, I might hit it even without auth if the view fails early, 
# OR I need to login first. Let's assume I need a valid token. 
# I'll borrow the login logic from a previous step or just rely on the user's report is usually not enough for details.)

# Actually, the user report IS the 500. I can just look at the code.
# But running a script is better to see the error.

import os

def login():
    # Attempt to login to get a token
    try:
        resp = requests.post("http://localhost:8000/api/v1/auth/login/", json={
            "username": "admin", "password": "admin_password" # Default?
        })
        if resp.status_code == 200:
            return resp.json()['access']
    except:
        pass
    return None

def trigger_delete_error():
    # Use a dummy ID that looks like the one in the error (4)
    doc_id = "4" 
    
    # Try with basic headers
    headers = {}
    
    # Try to get a token (assuming admin/admin for dev)
    token = login()
    if token:
        headers['Authorization'] = f"Bearer {token}"
    else:
        # Fallback to hardcoded commonly used one or just try without to see if it's an auth crash
        pass

    print(f"Attemping to DELETE {BASE_URL}/{doc_id}/ ...")
    resp = requests.delete(f"{BASE_URL}/{doc_id}/", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

if __name__ == "__main__":
    trigger_delete_error()
