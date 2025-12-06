
import requests
import json
import random

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "dev-token-bypass" # Assuming this works based on verification script
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

def get_patients():
    print("Fetching patients...")
    try:
        # Fetch a reasonable number of patients
        url = f"{BASE_URL}/patients/?page_size=50" 
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            results = r.json().get('results', [])
            print(f"Found {len(results)} patients.")
            return results
        else:
            print(f"Error fetching patients: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print(f"Exception fetching patients: {e}")
        return []

def get_available_beds():
    print("Fetching location hierarchy to find available beds...")
    beds = []
    try:
        r = requests.get(f"{BASE_URL}/ipd/locations/", headers=HEADERS)
        if r.status_code == 200:
            locations = r.json()
            
            # Recursive function to find beds
            def find_beds(nodes):
                for node in nodes:
                    # Check if it is a bed (physicalType coding 'bd' OR purely based on hierarchy if type missing)
                    is_bed = False
                    if node.get('physicalType') and node['physicalType'].get('coding'):
                        for code in node['physicalType']['coding']:
                            if code.get('code') == 'bd':
                                is_bed = True
                                break
                    
                    # Alternatively check naming convention if type is missing (fallback)
                    if not is_bed and (node['name'].startswith('Leito') or node['name'].startswith('Bed')):
                        is_bed = True

                    if is_bed:
                        # Check status
                        if node.get('status_code') == 'U': # Unoccupied
                            beds.append(node)
                    
                    # Recurse
                    if node.get('children'):
                        find_beds(node['children'])

            find_beds(locations)
            print(f"Found {len(beds)} available beds.")
            return beds
        else:
            print(f"Error fetching locations: {r.status_code} - {r.text}")
            return []
    except Exception as e:
        print(f"Exception fetching beds: {e}")
        return []

def admit_patients(patients, beds):
    print("\nStarting admission process...")
    # Shuffle to simulate random admissions
    random.shuffle(patients)
    
    count = 0
    max_admissions = min(len(patients), len(beds))
    
    if max_admissions == 0:
        print("No patients or no beds available to match.")
        return

    for i in range(max_admissions):
        patient = patients[i]
        bed = beds[i]
        
        print(f"Admitting {patient['name']} (ID: {patient['id']}) to {bed['name']} (ID: {bed['id']})...")
        
        payload = {
            "patient_id": patient['id'],
            "location_id": bed['id']
        }
        
        try:
            r = requests.post(f"{BASE_URL}/ipd/admit/", json=payload, headers=HEADERS)
            if r.status_code in [200, 201]:
                print(f"  -> Success")
                count += 1
            else:
                print(f"  -> Failed: {r.status_code} - {r.text}")
        except Exception as e:
             print(f"  -> Exception: {e}")

    print(f"\nTotal admissions processed: {count}")

if __name__ == "__main__":
    patients = get_patients()
    beds = get_available_beds()
    admit_patients(patients, beds)
