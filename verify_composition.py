import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = "http://localhost:8000/api/v1/auth/login/"
PDF_OUTPUT_DIR = "generated_pdfs"

if not os.path.exists(PDF_OUTPUT_DIR):
    os.makedirs(PDF_OUTPUT_DIR)

def get_token():
    print("Authenticating...")
    # Using bypass credentials
    response = requests.post(AUTH_URL, json={"username": "contato@ivonmatos.com.br", "password": "Protonsysdba@1986"})
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("access")
    else:
        print(f"Authentication failed: {response.text}")
        exit(1)

def verify_composition():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Create Composition
    print("\n[TEST] Creating Clinical Document (Composition)...")
    doc_data = {
        "patient_id": "patient-1",
        "doc_type": "anamnese",
        "title": "Anamnese de Teste Automatizado",
        "text_content": "<h1>Anamnese</h1><p>Paciente relata dores de cabeça frequentes.</p><p><b>Diagnóstico:</b> Cefaleia tensional.</p>"
    }
    
    response = requests.post(f"{BASE_URL}/documents/", json=doc_data, headers=headers)
    if response.status_code == 201:
        result = response.json()
        doc_id = result.get("id")
        print(f"✅ Composition Created. ID: {doc_id}")
    else:
        print(f"❌ Creation failed: {response.status_code} - {response.text}")
        return

    # 2. Generate PDF
    print(f"\n[TEST] Generating PDF for Document {doc_id}...")
    pdf_url = f"{BASE_URL}/documents/{doc_id}/pdf/"
    
    response = requests.get(pdf_url, headers=headers)
    
    if response.status_code == 200 and response.headers.get('content-type') == 'application/pdf':
        filename = f"{PDF_OUTPUT_DIR}/document_{doc_id}.pdf"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ PDF Generated and saved to: {filename}", flush=True)
        print(f"   Size: {len(response.content)} bytes", flush=True)
        if os.path.exists(filename):
             print("✅ File verification: EXISTS", flush=True)
    else:
        print(f"❌ PDF Generation failed: {response.status_code}", flush=True)
        print(response.text[:200], flush=True)

if __name__ == "__main__":
    verify_composition()
