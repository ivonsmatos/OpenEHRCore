
import requests
import json

token = "dev-token-bypass"
base_url = "http://localhost:8000/api/v1/ipd"

print("--- Testing Bed Management API ---")

# 1. List Locations
print("\n[1] Listing Location Hierarchy...")
try:
    r = requests.get(f"{base_url}/locations/", headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Top level nodes: {len(data)}")
        if data:
            hospital = data[0]
            print(f"Hospital: {hospital['name']}")
            print(f"Wards: {len(hospital.get('children', []))}")
            # Find a free bed
            target_bed_id = None
            if hospital.get('children'):
                ward = hospital['children'][0]
                if ward.get('children'):
                    # Room or Bed? Structure is Ward -> Room -> Bed or Ward -> Bed
                    # My seed creates Room.
                    first_child = ward['children'][0]
                    if first_child['name'].startswith("Quarto") or first_child['name'].startswith("Box"):
                         if first_child.get('children'):
                             bed = first_child['children'][0]
                             target_bed_id = bed['id']
                             print(f"Found Target Bed: {bed['name']} (ID: {target_bed_id})")
    else:
        print(r.text)
        target_bed_id = None
except Exception as e:
    print(f"Error: {e}")
    target_bed_id = None

# 2. Get Occupancy (Before)
print("\n[2] Checking Occupancy (Before Advisory)...")
try:
    r = requests.get(f"{base_url}/occupancy/", headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"Error: {e}")

# 3. Admit Patient
if target_bed_id:
    print(f"\n[3] Admitting Patient to Bed {target_bed_id}...")
    try:
        payload = {
            "patient_id": "1", # Assuming patient 1 exists from previous seeds
            "location_id": target_bed_id
        }
        r = requests.post(f"{base_url}/admit/", json=payload, headers={'Authorization': f'Bearer {token}'})
        print(f"Status: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"Error: {e}")

# 4. Get Occupancy (After)
print("\n[4] Checking Occupancy (After Advisory)...")
try:
    r = requests.get(f"{base_url}/occupancy/", headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
