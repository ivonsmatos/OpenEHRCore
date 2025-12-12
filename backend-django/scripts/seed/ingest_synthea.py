import os
import json
import requests
import time

FHIR_URL = "http://localhost:8080/fhir"
DATASET_PATH = r"C:\Users\ivonm\.cache\kagglehub\datasets\krsna540\synthea-dataset-jsons-ehr\versions\1\fhir"
LIMIT = 50

def ingest_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        # O Synthea gera Bundles do tipo 'transaction' ou 'collection'.
        # Se for transaction, podemos postar diretamente na raiz.
        
        # Assegurar que é um transaction para ingestão em lote
        if bundle.get('resourceType') == 'Bundle':
            bundle['type'] = 'transaction'
            
            # Add request method to each entry
            if 'entry' in bundle:
                for entry in bundle['entry']:
                    resource = entry.get('resource')
                    if resource:
                        # Use POST to create resources, letting server assign IDs if needed
                        # Or use PUT if we want to preserve IDs (Synthea uses UUIDs)
                        # Let's try PUT with the UUID relative URL to maintain internal references
                        entry['request'] = {
                            'method': 'POST',
                            'url': resource['resourceType']
                        }
                        
            # Postar o bundle inteiro
            r = requests.post(FHIR_URL, json=bundle, headers={'Content-Type': 'application/fhir+json'})
            
            if r.status_code in [200, 201]:
                print(f" [OK] {os.path.basename(filepath)}")
                return True
            else:
                print(f" [ERR] {os.path.basename(filepath)} - Status: {r.status_code}")
                print(f" --- RESP --- {r.text[:500]}")
                return False
    except Exception as e:
        print(f" [EXC] {os.path.basename(filepath)} - {e}")
        return False

def main():
    print(f"Iniciando ingestão de dados Synthea para {FHIR_URL}...")
    print(f"Buscando arquivos em: {DATASET_PATH}")
    
    count = 0
    success = 0
    
    for root, dirs, files in os.walk(DATASET_PATH):
        for file in files:
            if file.endswith(".json"):
                if ingest_file(os.path.join(root, file)):
                    success += 1
                
                count += 1
                if count >= LIMIT:
                    print(f"\nLimite de {LIMIT} arquivos atingido.")
                    print(f"Sucesso: {success}/{count}")
                    return

    print(f"\nFinalizado. Sucesso: {success}/{count}")

if __name__ == "__main__":
    main()
