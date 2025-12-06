
import os
import requests
import json
import random
from datetime import datetime
import concurrent.futures

FHIR_URL = "http://localhost:8080/fhir"
HEADERS = {"Content-Type": "application/fhir+json"}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_patients():
    resp = requests.get(f"{FHIR_URL}/Patient?_count=100")
    if resp.status_code != 200:
        return []
    bundle = resp.json()
    return [e['resource'] for e in bundle.get('entry', [])]

def create_composition(patient):
    pid = patient['id']
    name = "Unknown"
    if 'name' in patient:
        name = f"{patient['name'][0].get('given', [''])[0]} {patient['name'][0].get('family', '')}"
    
    # Types of documents to simulate
    doc_types = [
        {"code": "11506-3", "display": "Progress note", "title": f"Evolução Médica - {name}"},
        {"code": "18842-5", "display": "Discharge summary", "title": f"Sumário de Alta - {name}"},
        {"code": "57133-1", "display": "Referral note", "title": f"Encaminhamento - {name}"}
    ]
    
    # Pick 1 or 2 random documents
    selected_types = random.sample(doc_types, k=random.randint(1, 2))
    
    for dt in selected_types:
        composition = {
            "resourceType": "Composition",
            "status": "final",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": dt['code'],
                    "display": dt['display']
                }]
            },
            "subject": {"reference": f"Patient/{pid}", "display": name},
            "date": datetime.now().isoformat(),
            "author": [{"display": "Dr. AI Generator"}], # Mock author
            "title": dt['title'],
            "section": [
                {
                    "title": "Clinical Narrative",
                    "text": {
                        "status": "generated",
                        "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">Generated document for {name}. Patient appears stable. Continuity of care recommended.</div>"
                    }
                }
            ]
        }
        
        try:
            r = requests.post(f"{FHIR_URL}/Composition", json=composition, headers=HEADERS)
            if r.status_code in [200, 201]:
                # log(f"Created {dt['display']} for {name}")
                pass
            else:
                log(f"Failed to create doc for {pid}: {r.status_code} {r.text}")
        except Exception as e:
            log(f"Error creating doc: {e}")

def main():
    log("Fetching patients...")
    patients = get_patients()
    log(f"Found {len(patients)} patients. Generating documents...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_composition, p) for p in patients]
        for f in concurrent.futures.as_completed(futures):
            pass
            
    log("Document generation complete.")

if __name__ == "__main__":
    main()
