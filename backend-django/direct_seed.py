
import requests
import random
import json

FHIR_BASE = "http://localhost:8080/fhir"

def seed_beds():
    print(f"Connecting to FHIR at {FHIR_BASE}...")
    
    # 1. Fetch Beds
    try:
        r = requests.get(f"{FHIR_BASE}/Location", params={'_count': 1000}, headers={'Accept': 'application/fhir+json'})
        if r.status_code != 200:
            print(f"Failed to connect: {r.status_code}")
            return
    except Exception as e:
        print(f"Connection error: {e}")
        return

    bundle = r.json()
    entries = bundle.get('entry', [])
    all_locs = [e['resource'] for e in entries]
    
    beds = [
        l for l in all_locs 
        if l.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' 
        or l.get('name', '').startswith('Leito')
    ]
    
    print(f"Found {len(beds)} beds.")
    
    start_count = len(beds)
    needed = (13 + 9 + 23) - start_count
    
    if needed > 0:
        print(f"Creating {needed} new beds...")
        # Create a container Ward if possible or just beds?
        # Let's create a 'Expansion Ward'
        ward_data = {
            "resourceType": "Location",
            "name": "Ala de Expansão",
            "mode": "instance",
            "status": "active",
            "physicalType": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": "wa", "display": "Ward"}]
            }
        }
        r = requests.post(f"{FHIR_BASE}/Location", json=ward_data, headers={'Content-Type': 'application/fhir+json'})
        if r.status_code in [200, 201]:
            ward_id = r.json()['id']
            print(f"Created Expansion Ward: {ward_id}")
            
            for i in range(needed):
                bed_name = f"Leito Exp-{i+1}"
                bed_data = {
                    "resourceType": "Location",
                    "name": bed_name,
                    "mode": "instance",
                    "status": "active",
                    "partOf": {"reference": f"Location/{ward_id}"},
                    "physicalType": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": "bd", "display": "Bed"}]
                    },
                    "operationalStatus": {
                         "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                         "code": "U", 
                         "display": "Unoccupied"
                    }
                }
                requests.post(f"{FHIR_BASE}/Location", json=bed_data, headers={'Content-Type': 'application/fhir+json'})
                # We need to re-fetch/add to list? No, just rely on next fetch or add dummy?
                # Actually, effectively we can just create them with the target status immediately?
                # But my update logic below handles randomization.
                # Let's just create them as 'U' and then re-fetch all beds to include them in shuffle.
        else:
             print("Failed to create ward.")

        # Re-fetch to include new beds
        r = requests.get(f"{FHIR_BASE}/Location", params={'_count': 1000}, headers={'Accept': 'application/fhir+json'})
        entries = r.json().get('entry', [])
        all_locs = [e['resource'] for e in entries]
        beds = [
            l for l in all_locs 
            if l.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' 
            or l.get('name', '').startswith('Leito')
        ]
        print(f"Total beds after creation: {len(beds)}")

    random.shuffle(beds)
    
    target_occupied = 13
    target_cleaning = 9
    
    idx = 0
    occupied = beds[idx : idx + target_occupied]
    idx += target_occupied
    
    cleaning = beds[idx : idx + target_cleaning]
    idx += target_cleaning
    
    free = beds[idx:]
    
    print(f"Assigning -> Occupied: {len(occupied)}, Cleaning: {len(cleaning)}, Free: {len(free)}")

    def update(bed_list, code, display):
        for bed in bed_list:
            bed['operationalStatus'] = {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                "code": code,
                "display": display
            }
            url = f"{FHIR_BASE}/Location/{bed['id']}"
            resp = requests.put(url, json=bed, headers={'Content-Type': 'application/fhir+json'})
            if resp.status_code not in [200, 201]:
                print(f"Failed {bed['id']}: {resp.status_code}")

    update(occupied, 'O', 'Occupied')
    update(cleaning, 'K', 'Contaminated')
    update(free, 'U', 'Unoccupied')

    print("Direct seed complete.")

if __name__ == "__main__":
    seed_beds()
