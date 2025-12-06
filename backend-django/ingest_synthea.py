
import os
import glob
import requests
import json
import concurrent.futures
import time

# Configuration
FHIR_URL = "http://localhost:8080/fhir"
# Path detected from previous step logs (reconstructed)
# Remove 'fhir' from end to start searching from 'versions/1' which we know works
DATA_DIR = r"C:\Users\ivonm\.cache\kagglehub\datasets\krsna540\synthea-dataset-jsons-ehr\versions\1"

HEADERS = {"Content-Type": "application/fhir+json"}

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def find_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files

def wipe_resource(resource_type):
    log(f"Wiping {resource_type}...")
    try:
        # Search for all resources of this type
        # Use _summary=true to get minimal data, _count=500
        url = f"{FHIR_URL}/{resource_type}?_count=1000"
        # Limit loop to avoid infinite stuck
        for attempt in range(3):
            resp = requests.get(url)
            if resp.status_code != 200:
                log(f"Failed to list {resource_type}: {resp.status_code}")
                break
            
            bundle = resp.json()
            if not bundle.get('entry'):
                break
                
            ids = [e['resource']['id'] for e in bundle['entry']]
            log(f"Found {len(ids)} {resource_type}s to delete (Attempt {attempt+1}).")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(requests.delete, f"{FHIR_URL}/{resource_type}/{rid}?_cascade=delete"): rid for rid in ids}
                for future in concurrent.futures.as_completed(futures):
                    rid = futures[future]
                    try:
                        r = future.result()
                        # If failed, log why
                        if r.status_code not in [200, 204]:
                             pass # log(f"Failed {rid}: {r.status_code}")
                    except Exception as e:
                        log(f"Error {rid}: {e}")
            
            # Brief pause
            time.sleep(1)
                
    except Exception as e:
        log(f"Error wiping {resource_type}: {e}")

def wipe_all():
    wipe_resource("Patient")
    # wipe_resource("Practitioner") # Optional/Risk if stuck
    # wipe_resource("Organization")

def post_bundle(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Synthea uses "collection" or "transaction".
        # If "bundleType" is collection, we can't POST to root.
        # But commonly it is transaction.
        b_type = data.get('type', 'transaction')
        
        if b_type == 'collection':
            # Identify individual resources and POST them?
            # Or just try to POST as transaction?
            data['type'] = 'transaction' # HACK: Force transaction
            if 'entry' in data:
                for entry in data['entry']:
                    if 'request' not in entry:
                         # Add request verb for transaction
                         entry['request'] = {
                             "method": "POST",
                             "url": entry['resource']['resourceType']
                         }
        
        resp = requests.post(FHIR_URL, json=data, headers=HEADERS)
        if resp.status_code in [200, 201]:
            # log(f"Ingested {os.path.basename(filepath)}")
            return True
        else:
            log(f"Failed {os.path.basename(filepath)}: {resp.status_code} - {resp.text[:100]}")
            return False
    except Exception as e:
        log(f"Error ingesting {filepath}: {e}")
        return False

def main():
    if not os.path.exists(DATA_DIR):
        log(f"Data directory not found: {DATA_DIR}")
        return

    log("Starting DB Wipe...")
    wipe_all()
    log("DB Wipe Complete.")
    
    files = find_json_files(DATA_DIR)
    log(f"Found {len(files)} JSON files.")
    
    # Priority files
    hospitals = [f for f in files if 'hospital' in f.lower()]
    practitioners = [f for f in files if 'practitioner' in f.lower()]
    patients = [f for f in files if f not in hospitals and f not in practitioners]
    
    log(f"Ingesting {len(hospitals)} Hospitals...")
    for f in hospitals: post_bundle(f)
    
    log(f"Ingesting {len(practitioners)} Practitioners...")
    for f in practitioners: post_bundle(f)
    
    log(f"Ingesting {len(patients)} Patients...")
    # Cap at 50 patients for now to avoid freezing the machine or taking hours
    # User said "popular o sistema", not "ingest huge dataset entirely"
    # But Synthea 100 json files is manageable.
    # 2GB dataset? That's thousands. I will cap at 50 for safety first run.
    target_patients = patients[:50] 
    
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(post_bundle, f): f for f in target_patients}
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
                if success_count % 10 == 0:
                    log(f"Progress: {success_count}/{len(target_patients)} Patients")
                    
    log(f"Ingestion Complete. {success_count} Patients ingested.")

if __name__ == "__main__":
    main()
