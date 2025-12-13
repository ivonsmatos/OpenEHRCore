"""Test Analytics API"""
import requests

# First login to get token
login_resp = requests.post(
    "http://localhost:8000/api/v1/auth/login/",
    json={
        "username": "contato@ivonmatos.com.br",
        "password": "Protonsysdba@1986"
    }
)

if login_resp.status_code == 200:
    token = login_resp.json().get("access_token")
    print(f"✅ Login OK, token: {token[:30]}...")
    
    # Test KPI endpoint
    headers = {"Authorization": f"Bearer {token}"}
    kpi_resp = requests.get(
        "http://localhost:8000/api/v1/analytics/kpi/",
        headers=headers
    )
    
    print(f"\n📊 KPI Response ({kpi_resp.status_code}):")
    if kpi_resp.status_code == 200:
        data = kpi_resp.json()
        print(f"  - Novos Pacientes: {data.get('new_patients')}")
        print(f"  - Ambulatório: {data.get('opd_patients')}")
        print(f"  - Cirurgias: {data.get('todays_operations')}")
        print(f"  - Visitantes: {data.get('visitors')}")
    else:
        print(f"  Error: {kpi_resp.text[:200]}")
        
    # Test Admissions endpoint
    adm_resp = requests.get(
        "http://localhost:8000/api/v1/analytics/admissions/",
        headers=headers
    )
    print(f"\n🏥 Admissions Response ({adm_resp.status_code}):")
    if adm_resp.status_code == 200:
        admissions = adm_resp.json()
        print(f"  - Total admissions: {len(admissions)}")
        if admissions:
            print(f"  - First: {admissions[0].get('name', 'N/A')}")
    else:
        print(f"  Error: {adm_resp.text[:200]}")
        
else:
    print(f"❌ Login failed: {login_resp.status_code}")
    print(login_resp.text[:200])
