
import os
import django
import random
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from fhir_api.utils import FHIRService

def update_bed_statuses():
    fhir = FHIRService()
    
    # Fetch all locations
    print("Fetching locations...")
    all_locs = fhir.search_resources('Location', {'_count': 1000})
    
    # Filter for beds
    beds = [
        l for l in all_locs 
        if l.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' 
        or l.get('name', '').startswith('Leito')
    ]
    
    print(f"Found {len(beds)} beds.")
    
    # Target counts
    target_occupied = 13
    target_cleaning = 9
    # Rest are free
    
    if len(beds) < (target_occupied + target_cleaning):
        print("Not enough beds to satisfy request! Creating more...")
        # (Optional: logic to create more beds, but for now we'll just use what we have or warn)
        # We will just fill as much as possible
        pass

    random.shuffle(beds)
    
    occupied_beds = beds[:target_occupied]
    cleaning_beds = beds[target_occupied : target_occupied+target_cleaning]
    free_beds = beds[target_occupied+target_cleaning:]
    
    print(f"Assigning: {len(occupied_beds)} Occupied, {len(cleaning_beds)} Cleaning, {len(free_beds)} Free")
    
    def update_status(bed_list, status_code, status_display):
        for bed in bed_list:
            bed['operationalStatus'] = {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                "code": status_code,
                "display": status_display
            }
            # PUT update
            url = f"{fhir.base_url}/Location/{bed['id']}"
            resp = requests.put(url, json=bed, headers={'Content-Type': 'application/fhir+json'})
            if resp.status_code not in [200, 201]:
                print(f"Failed to update {bed['name']}: {resp.status_code}")
                
    update_status(occupied_beds, 'O', 'Occupied')
    update_status(cleaning_beds, 'K', 'Contaminated')
    update_status(free_beds, 'U', 'Unoccupied')
    
    print("Done updating bed statuses.")

if __name__ == "__main__":
    update_bed_statuses()
