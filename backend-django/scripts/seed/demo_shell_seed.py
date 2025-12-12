
from fhir_api.utils import FHIRService
import requests
import random

def seed_beds():
    print("Starting bed seed...")
    fhir = FHIRService()
    
    # 1. Fetch Beds
    all_locs = fhir.search_resources('Location', {'_count': 1000})
    beds = [
        l for l in all_locs 
        if l.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' 
        or l.get('name', '').startswith('Leito')
    ]
    print(f"Found {len(beds)} beds.")

    if not beds:
        print("No beds found to update.")
        return

    # 2. Shuffle and Assign
    random.shuffle(beds)
    
    target_occupied = 13
    target_cleaning = 9
    
    idx = 0
    occupied = beds[idx : idx + target_occupied]
    idx += target_occupied
    
    cleaning = beds[idx : idx + target_cleaning]
    idx += target_cleaning
    
    free = beds[idx:]
    
    print(f"Counts -> Occupied: {len(occupied)}, Cleaning: {len(cleaning)}, Free: {len(free)}")

    # 3. Update Function
    def update(bed_list, code, display):
        for bed in bed_list:
            # Check if already correct to save time? No, force update.
            bed['operationalStatus'] = {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                "code": code,
                "display": display
            }
            # Put
            url = f"{fhir.base_url}/Location/{bed['id']}"
            try:
                r = requests.put(url, json=bed, headers={'Content-Type': 'application/fhir+json'})
                if r.status_code not in [200, 201]:
                     print(f"Error updating {bed['name']}: {r.status_code}")
            except Exception as e:
                print(f"Exception updating {bed['name']}: {e}")

    # 4. Execute Updates
    update(occupied, 'O', 'Occupied')
    update(cleaning, 'K', 'Contaminated')
    update(free, 'U', 'Unoccupied')
    
    print("Seed complete.")

seed_beds()
