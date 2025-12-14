"""
Create beds with Housekeeping and Maintenance status
"""
import requests

FHIR_URL = 'http://localhost:8080/fhir'
HEADERS = {'Content-Type': 'application/fhir+json'}

# Leitos em Higienização (status H = Housekeeping)
housekeeping_beds = [
    {'name': 'Leito Comum 101 - Em Higienização', 'status': 'H', 'display': 'Housekeeping'},
    {'name': 'Leito Comum 102 - Em Higienização', 'status': 'H', 'display': 'Housekeeping'},
    {'name': 'Leito UTI 201 - Em Higienização', 'status': 'H', 'display': 'Housekeeping'},
]

# Leitos Bloqueados/Manutenção (status C = Closed)
blocked_beds = [
    {'name': 'Leito Comum 103 - Bloqueado Manutenção', 'status': 'C', 'display': 'Closed'},
    {'name': 'Leito Comum 104 - Bloqueado Manutenção', 'status': 'C', 'display': 'Closed'},
    {'name': 'Leito Cirúrgico 301 - Bloqueado', 'status': 'C', 'display': 'Closed'},
    {'name': 'Sala Cirúrgica 401 - Manutenção', 'status': 'C', 'display': 'Closed'},
]

all_beds = housekeeping_beds + blocked_beds

for bed in all_beds:
    location = {
        'resourceType': 'Location',
        'status': 'active' if bed['status'] == 'H' else 'inactive',
        'operationalStatus': {
            'system': 'http://terminology.hl7.org/CodeSystem/v2-0116',
            'code': bed['status'],
            'display': bed['display']
        },
        'name': bed['name'],
        'mode': 'instance',
        'type': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/location-physical-type', 'code': 'bd', 'display': 'Bed'}]}],
        'physicalType': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/location-physical-type', 'code': 'bd', 'display': 'Bed'}]}
    }
    
    response = requests.post(f'{FHIR_URL}/Location', json=location, headers=HEADERS, timeout=10)
    if response.status_code in [200, 201]:
        print(f'Created: {bed["name"]} (ID: {response.json().get("id")})')
    else:
        print(f'Failed: {bed["name"]}')

print('\nDone!')
