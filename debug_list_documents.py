
import requests
import json

FHIR_URL = "http://localhost:8080/fhir/Composition"

def debug_list_documents():
    print("--- 1. Listing ALL Compositions (no params) ---")
    try:
        resp = requests.get(FHIR_URL, headers={'Cache-Control': 'no-cache'})
        if resp.status_code == 200:
            bundle = resp.json()
            total = bundle.get('total', 'Unknown')
            limit = len(bundle.get('entry', []))
            print(f"Total reported: {total}")
            print(f"Entries in this page: {limit}")
            
            for i, entry in enumerate(bundle.get('entry', [])):
                res = entry['resource']
                print(f" [{i}] ID: {res['id']}, Type: {res.get('type', {}).get('text')}, Date: {res.get('date')}")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

    print("\n--- 2. Listing with Sort Param (_sort=-date) ---")
    try:
        resp = requests.get(FHIR_URL, params={'_sort': '-date'})
        if resp.status_code == 200:
            bundle = resp.json()
            print(f"Entries returned: {len(bundle.get('entry', []))}")
        else:
            print(f"Error with sort: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_list_documents()
