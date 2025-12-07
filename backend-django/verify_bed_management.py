
import requests
import json
import time

token = "dev-token-bypass"
base_url = "http://localhost:8000/api/v1/ipd"
headers = {'Authorization': f'Bearer {token}'}

print("--- Testing Bed Management API ---")

# 1. List Locations
print("\n[1] Listing Location Hierarchy...")
target_bed_id = None
try:
    r = requests.get(f"{base_url}/locations/", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Top level nodes: {len(data)}")
        if data:
            hospital = data[0]
            print(f"Hospital: {hospital['name']}")
            print(f"Wards: {len(hospital.get('children', []))}")
            # Find a free bed
            
            # Simple recursive search for a free bed
            def find_free_bed(node):
                if (node.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' or node['name'].startswith('Leito')) and node.get('status_code') == 'U':
                    return node
                if node.get('children'):
                    for child in node['children']:
                        found = find_free_bed(child)
                        if found: return found
                return None

            bed = find_free_bed(hospital)
            if bed:
                 target_bed_id = bed['id']
                 print(f"Found Target Bed for Admission: {bed['name']} (ID: {target_bed_id})")
            else:
                 print("No free beds found in hierarchy.")
    else:
        print(r.text)
except Exception as e:
    print(f"Error: {e}")

# 2. Get Occupancy (Before)
print("\n[2] Checking Occupancy (Before)...")
try:
    r = requests.get(f"{base_url}/occupancy/", headers=headers)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# 3. Admit Patient
if target_bed_id:
    print(f"\n[3] Admitting Patient to Bed {target_bed_id}...")
    try:
        payload = {
            "patient_id": "1", # Assuming patient 1 exists
            "location_id": target_bed_id
        }
        r = requests.post(f"{base_url}/admit/", json=payload, headers=headers)
        print(f"Status: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"Error: {e}")

    # 4. Transfer Patient
    print("\n[4] Testing Patient Transfer ---")
    # Need to find ANOTHER free bed
    try:
        # Refresh locations to get updated status
        locs_res = requests.get(f"{base_url}/locations/", headers=headers)
        hospital_updated = locs_res.json()[0]
        
        def find_all_free_beds(node, exclude_id):
            beds = []
            if (node.get('physicalType', {}).get('coding', [{}])[0].get('code') == 'bd' or node['name'].startswith('Leito')) and node.get('status_code') == 'U':
                if node['id'] != exclude_id:
                     beds.append(node)
            if node.get('children'):
                for child in node['children']:
                    beds.extend(find_all_free_beds(child, exclude_id))
            return beds

        free_beds = find_all_free_beds(hospital_updated, target_bed_id)
        
        if not free_beds:
            print("No free beds available for transfer test.")
        else:
            transfer_target_bed_id = free_beds[0]['id']
            print(f"Transferring patient from {target_bed_id} to {transfer_target_bed_id} ({free_beds[0]['name']})...")
            
            transfer_res = requests.post(f"{base_url}/transfer/", json={
                'source_id': target_bed_id,
                'target_id': transfer_target_bed_id
            }, headers=headers)
            
            print(f"Transfer Status: {transfer_res.status_code}")
            print(transfer_res.text)
            
            if transfer_res.status_code == 200:
                print("Transfer successful!")
                target_bed_id = transfer_target_bed_id # Update for next steps if needed
            else:
                print(f"Transfer failed.")

        # 5. Block Bed
        print("\n[5] Testing Bed Blocking ---")
        # Reuse the list of free beds, pick another one
        # Refresh free beds list just in case
        free_beds_for_block = [b for b in free_beds if b['id'] != transfer_target_bed_id]
        
        if free_beds_for_block:
            block_target = free_beds_for_block[0]['id']
            print(f"Blocking bed {block_target} ({free_beds_for_block[0]['name']})...")
            block_res = requests.post(f"{base_url}/bed/{block_target}/block/", headers=headers)
            
            print(f"Block Status: {block_res.status_code}")
            print(block_res.json())
            
            if block_res.status_code == 200:
                # Unblock
                print("Unblocking same bed...")
                unblock_res = requests.post(f"{base_url}/bed/{block_target}/block/", headers=headers)
                print(f"Unblock Status: {unblock_res.status_code}")
                print(unblock_res.json())
            else:
                 print("Block failed.")
        else:
            print("No beds available for blocking test.")
            
    except Exception as e:
        print(f"Error during Transfer/Block: {e}")

# Final Stats
print("\n[Final] Checking Occupancy to verify states...")
try:
    r = requests.get(f"{base_url}/occupancy/", headers=headers)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
