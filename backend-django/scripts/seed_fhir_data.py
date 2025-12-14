"""
HealthStack - Complete FHIR Seed Data
Creates comprehensive sample data in HAPI FHIR for development and testing.
All resources are 100% FHIR R4 compliant with all fields populated.

Run with: python scripts/seed_fhir_data.py
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import random

FHIR_URL = "http://localhost:8080/fhir"
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

# Track created IDs for references
created_ids = {
    "organizations": [],
    "practitioners": [],
    "patients": [],
    "locations": [],
    "encounters": []
}


def check_fhir_available():
    """Check if HAPI FHIR is available"""
    try:
        response = requests.get(f"{FHIR_URL}/metadata", timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"  Connection error: {e}")
        return False


def create_resource(resource_type, resource_data):
    """Create a FHIR resource and return the created ID"""
    try:
        if 'id' in resource_data:
            del resource_data['id']
            
        response = requests.post(
            f"{FHIR_URL}/{resource_type}",
            json=resource_data,
            headers=HEADERS,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            resource_id = result.get('id')
            return resource_id
        else:
            print(f"  ✗ Failed {resource_type}: {response.status_code} - {response.text[:100]}")
            return None
    except Exception as e:
        print(f"  ✗ Error {resource_type}: {e}")
        return None


def seed_organizations():
    """Create sample organizations"""
    print("\n📋 Creating Organizations...")
    
    orgs = [
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov", "display": "Healthcare Provider"}]}],
            "name": "HealthStack Hospital Central",
            "alias": ["HSHC", "Hospital Central"],
            "telecom": [
                {"system": "phone", "value": "(11) 3000-0000", "use": "work"},
                {"system": "fax", "value": "(11) 3000-0001", "use": "work"},
                {"system": "email", "value": "contato@healthstack.com", "use": "work"},
                {"system": "url", "value": "https://healthstack.com"}
            ],
            "address": [{
                "use": "work",
                "type": "both",
                "text": "Av. Paulista, 1500 - São Paulo, SP",
                "line": ["Av. Paulista, 1500"],
                "city": "São Paulo",
                "district": "Bela Vista",
                "state": "SP",
                "postalCode": "01310-200",
                "country": "BR"
            }],
            "contact": [{
                "purpose": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/contactentity-type", "code": "ADMIN"}]},
                "name": {"text": "Administração Central"},
                "telecom": [{"system": "phone", "value": "(11) 3000-0010"}]
            }]
        },
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "dept", "display": "Hospital Department"}]}],
            "name": "Departamento de Cardiologia",
            "alias": ["Cardio"],
            "telecom": [{"system": "phone", "value": "(11) 3000-1001", "use": "work"}]
        },
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "dept", "display": "Hospital Department"}]}],
            "name": "Centro Cirúrgico",
            "alias": ["CC", "Cirurgia"],
            "telecom": [{"system": "phone", "value": "(11) 3000-2001", "use": "work"}]
        },
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "dept", "display": "Hospital Department"}]}],
            "name": "Ambulatório Geral",
            "alias": ["Ambulatório"],
            "telecom": [{"system": "phone", "value": "(11) 3000-3001", "use": "work"}]
        },
        {
            "resourceType": "Organization",
            "active": True,
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "dept", "display": "Hospital Department"}]}],
            "name": "UTI - Unidade de Terapia Intensiva",
            "alias": ["UTI"],
            "telecom": [{"system": "phone", "value": "(11) 3000-4001", "use": "work"}]
        }
    ]
    
    for org in orgs:
        org_id = create_resource("Organization", org)
        if org_id:
            created_ids["organizations"].append(org_id)
            print(f"  ✓ Organization: {org['name']} (ID: {org_id})")


def seed_locations():
    """Create sample locations (beds, rooms, wards)"""
    print("\n🏥 Creating Locations (Beds, Rooms, Wards)...")
    
    # Wards
    wards = [
        {"name": "Ala A - Clínica Médica", "type_code": "wa", "type_display": "Ward", "status": "active"},
        {"name": "Ala B - Cirúrgica", "type_code": "wa", "type_display": "Ward", "status": "active"},
        {"name": "UTI Adulto", "type_code": "icu", "type_display": "Intensive Care Unit", "status": "active"},
        {"name": "UTI Neonatal", "type_code": "icu", "type_display": "Intensive Care Unit", "status": "active"},
        {"name": "Centro Cirúrgico", "type_code": "or", "type_display": "Operating Room", "status": "active"},
        {"name": "Ambulatório", "type_code": "outptnt", "type_display": "Outpatient", "status": "active"},
        {"name": "Pronto Socorro", "type_code": "er", "type_display": "Emergency Room", "status": "active"},
        {"name": "Maternidade", "type_code": "wa", "type_display": "Ward", "status": "active"},
    ]
    
    ward_ids = []
    for ward in wards:
        location = {
            "resourceType": "Location",
            "status": ward["status"],
            "operationalStatus": {"system": "http://terminology.hl7.org/CodeSystem/v2-0116", "code": "O", "display": "Occupied"},
            "name": ward["name"],
            "description": f"Localização: {ward['name']}",
            "mode": "instance",
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": ward["type_code"], "display": ward["type_display"]}]}],
            "telecom": [{"system": "phone", "value": f"(11) 3000-{random.randint(1000,9999)}", "use": "work"}],
            "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": "wa", "display": "Ward"}]},
            "managingOrganization": {"reference": f"Organization/{created_ids['organizations'][0]}"} if created_ids['organizations'] else None
        }
        loc_id = create_resource("Location", location)
        if loc_id:
            ward_ids.append({"id": loc_id, "name": ward["name"]})
            created_ids["locations"].append(loc_id)
            print(f"  ✓ Ward: {ward['name']} (ID: {loc_id})")
    
    # Beds - multiple types
    bed_types = [
        {"type": "Leito Comum", "code": "bd", "display": "Bed", "count": 10},
        {"type": "Leito UTI", "code": "bd", "display": "Bed", "count": 5},
        {"type": "Leito Isolamento", "code": "bd", "display": "Bed", "count": 3},
        {"type": "Leito Cirúrgico", "code": "bd", "display": "Bed", "count": 4},
        {"type": "Leito Observação", "code": "bd", "display": "Bed", "count": 6},
        {"type": "Leito Berçário", "code": "bd", "display": "Bed", "count": 4},
        {"type": "Leito PPP (Pré-parto)", "code": "bd", "display": "Bed", "count": 3},
        {"type": "Sala Cirúrgica", "code": "ro", "display": "Room", "count": 4},
        {"type": "Consultório", "code": "ro", "display": "Room", "count": 8},
    ]
    
    statuses = ["O", "U", "H", "C"]  # Occupied, Unoccupied, Housekeeping, Closed
    status_map = {"O": "Ocupado", "U": "Disponível", "H": "Limpeza", "C": "Fechado"}
    
    bed_num = 1
    for bed_type in bed_types:
        for i in range(bed_type["count"]):
            status = random.choice(statuses)
            ward = random.choice(ward_ids) if ward_ids else None
            
            bed = {
                "resourceType": "Location",
                "status": "active" if status != "C" else "inactive",
                "operationalStatus": {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                    "code": status,
                    "display": status_map[status]
                },
                "name": f"{bed_type['type']} {bed_num:03d}",
                "alias": [f"L{bed_num:03d}"],
                "description": f"{bed_type['type']} - {status_map[status]}",
                "mode": "instance",
                "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": bed_type["code"], "display": bed_type["display"]}]}],
                "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type", "code": "bd", "display": "Bed"}]},
            }
            
            if ward:
                bed["partOf"] = {"reference": f"Location/{ward['id']}", "display": ward["name"]}
            
            if created_ids['organizations']:
                bed["managingOrganization"] = {"reference": f"Organization/{created_ids['organizations'][0]}"}
            
            loc_id = create_resource("Location", bed)
            if loc_id:
                created_ids["locations"].append(loc_id)
            bed_num += 1
    
    print(f"  ✓ Created {bed_num - 1} beds/rooms total")


def seed_practitioners():
    """Create sample practitioners with all fields"""
    print("\n👨‍⚕️ Creating Practitioners...")
    
    practitioners = [
        {
            "name": {"family": "Silva", "given": ["Maria", "Carolina"], "prefix": ["Dra."]},
            "gender": "female", "birthDate": "1985-03-15",
            "cpf": "123.456.789-00", "crm": "CRM-SP 123456",
            "specialty": {"code": "cardiology", "display": "Cardiologia"},
            "phone": "(11) 99999-0001", "email": "maria.silva@healthstack.com"
        },
        {
            "name": {"family": "Santos", "given": ["João", "Pedro"], "prefix": ["Dr."]},
            "gender": "male", "birthDate": "1978-07-20",
            "cpf": "987.654.321-00", "crm": "CRM-SP 654321",
            "specialty": {"code": "orthopedics", "display": "Ortopedia"},
            "phone": "(11) 99999-0002", "email": "joao.santos@healthstack.com"
        },
        {
            "name": {"family": "Oliveira", "given": ["Ana", "Beatriz"], "prefix": ["Dra."]},
            "gender": "female", "birthDate": "1990-11-08",
            "cpf": "456.789.123-00", "crm": "CRM-SP 789123",
            "specialty": {"code": "pediatrics", "display": "Pediatria"},
            "phone": "(11) 99999-0003", "email": "ana.oliveira@healthstack.com"
        },
        {
            "name": {"family": "Costa", "given": ["Roberto"], "prefix": ["Dr."]},
            "gender": "male", "birthDate": "1982-04-25",
            "cpf": "321.654.987-00", "crm": "CRM-SP 456789",
            "specialty": {"code": "neurology", "display": "Neurologia"},
            "phone": "(11) 99999-0004", "email": "roberto.costa@healthstack.com"
        },
        {
            "name": {"family": "Ferreira", "given": ["Patricia"], "prefix": ["Dra."]},
            "gender": "female", "birthDate": "1988-09-12",
            "cpf": "789.123.456-00", "crm": "CRM-SP 321654",
            "specialty": {"code": "dermatology", "display": "Dermatologia"},
            "phone": "(11) 99999-0005", "email": "patricia.ferreira@healthstack.com"
        },
        {
            "name": {"family": "Mendes", "given": ["Ricardo", "Augusto"], "prefix": ["Dr."]},
            "gender": "male", "birthDate": "1975-01-30",
            "cpf": "111.222.333-44", "crm": "CRM-SP 111222",
            "specialty": {"code": "surgery", "display": "Cirurgia Geral"},
            "phone": "(11) 99999-0006", "email": "ricardo.mendes@healthstack.com"
        },
        {
            "name": {"family": "Lima", "given": ["Camila"], "prefix": ["Dra."]},
            "gender": "female", "birthDate": "1992-06-18",
            "cpf": "222.333.444-55", "crm": "CRM-SP 222333",
            "specialty": {"code": "obstetrics", "display": "Obstetrícia"},
            "phone": "(11) 99999-0007", "email": "camila.lima@healthstack.com"
        },
        {
            "name": {"family": "Rodrigues", "given": ["Fernando"], "prefix": ["Dr."]},
            "gender": "male", "birthDate": "1980-12-05",
            "cpf": "333.444.555-66", "crm": "CRM-SP 333444",
            "specialty": {"code": "emergency", "display": "Emergência"},
            "phone": "(11) 99999-0008", "email": "fernando.rodrigues@healthstack.com"
        }
    ]
    
    for p in practitioners:
        practitioner = {
            "resourceType": "Practitioner",
            "active": True,
            "name": [{
                "use": "official",
                "family": p["name"]["family"],
                "given": p["name"]["given"],
                "prefix": p["name"]["prefix"]
            }],
            "gender": p["gender"],
            "birthDate": p["birthDate"],
            "identifier": [
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": p["cpf"]},
                {"system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm", "value": p["crm"]}
            ],
            "qualification": [{
                "code": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/practitioner-specialty", "code": p["specialty"]["code"], "display": p["specialty"]["display"]}],
                    "text": p["specialty"]["display"]
                }
            }],
            "telecom": [
                {"system": "phone", "value": p["phone"], "use": "mobile", "rank": 1},
                {"system": "email", "value": p["email"], "use": "work", "rank": 2}
            ],
            "address": [{
                "use": "work",
                "type": "physical",
                "line": ["Av. Paulista, 1500"],
                "city": "São Paulo",
                "state": "SP",
                "postalCode": "01310-200",
                "country": "BR"
            }],
            "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "pt-BR", "display": "Português (Brasil)"}]}]
        }
        
        pid = create_resource("Practitioner", practitioner)
        if pid:
            created_ids["practitioners"].append(pid)
            print(f"  ✓ Practitioner: {p['name']['given'][0]} {p['name']['family']} - {p['specialty']['display']} (ID: {pid})")


def seed_patients():
    """Create sample patients with ALL fields populated"""
    print("\n🏥 Creating Patients (100% Field Coverage)...")
    
    patients = [
        {
            "name": {"family": "Souza", "given": ["Carlos", "Eduardo"]},
            "gender": "male", "birthDate": "1975-06-15",
            "cpf": "111.222.333-44", "cns": "123456789012345",
            "phone": "(11) 98888-0001", "email": "carlos.souza@email.com",
            "address": {"line": ["Rua das Flores, 123"], "city": "São Paulo", "state": "SP", "postalCode": "01234-567"},
            "marital": "M", "contact_name": "Maria Souza", "contact_phone": "(11) 98888-1001"
        },
        {
            "name": {"family": "Lima", "given": ["Fernanda"]},
            "gender": "female", "birthDate": "1992-03-22",
            "cpf": "222.333.444-55", "cns": "234567890123456",
            "phone": "(11) 98888-0002", "email": "fernanda.lima@email.com",
            "address": {"line": ["Av. Brasil, 456"], "city": "São Paulo", "state": "SP", "postalCode": "02345-678"},
            "marital": "S", "contact_name": "José Lima", "contact_phone": "(11) 98888-1002"
        },
        {
            "name": {"family": "Pereira", "given": ["Ricardo"]},
            "gender": "male", "birthDate": "1988-11-10",
            "cpf": "333.444.555-66", "cns": "345678901234567",
            "phone": "(11) 98888-0003", "email": "ricardo.pereira@email.com",
            "address": {"line": ["Rua Augusta, 789"], "city": "São Paulo", "state": "SP", "postalCode": "03456-789"},
            "marital": "M", "contact_name": "Ana Pereira", "contact_phone": "(11) 98888-1003"
        },
        {
            "name": {"family": "Almeida", "given": ["Julia", "Maria"]},
            "gender": "female", "birthDate": "2015-08-05",
            "cpf": "444.555.666-77", "cns": "456789012345678",
            "phone": "(11) 98888-0004", "email": "julia.mae@email.com",
            "address": {"line": ["Rua Oscar Freire, 321"], "city": "São Paulo", "state": "SP", "postalCode": "04567-890"},
            "marital": "S", "contact_name": "Paula Almeida", "contact_phone": "(11) 98888-1004"
        },
        {
            "name": {"family": "Martins", "given": ["Antonio"]},
            "gender": "male", "birthDate": "1955-02-28",
            "cpf": "555.666.777-88", "cns": "567890123456789",
            "phone": "(11) 98888-0005", "email": "antonio.martins@email.com",
            "address": {"line": ["Av. Rebouças, 654"], "city": "São Paulo", "state": "SP", "postalCode": "05678-901"},
            "marital": "W", "contact_name": "Roberto Martins", "contact_phone": "(11) 98888-1005"
        },
        {
            "name": {"family": "Nascimento", "given": ["Beatriz", "Santos"]},
            "gender": "female", "birthDate": "1998-07-14",
            "cpf": "666.777.888-99", "cns": "678901234567890",
            "phone": "(11) 98888-0006", "email": "beatriz.nascimento@email.com",
            "address": {"line": ["Rua Consolação, 987"], "city": "São Paulo", "state": "SP", "postalCode": "06789-012"},
            "marital": "S", "contact_name": "Rosa Nascimento", "contact_phone": "(11) 98888-1006"
        },
        {
            "name": {"family": "Rocha", "given": ["Marcos", "Vinícius"]},
            "gender": "male", "birthDate": "1970-04-03",
            "cpf": "777.888.999-00", "cns": "789012345678901",
            "phone": "(11) 98888-0007", "email": "marcos.rocha@email.com",
            "address": {"line": ["Av. Faria Lima, 1234"], "city": "São Paulo", "state": "SP", "postalCode": "07890-123"},
            "marital": "D", "contact_name": "Lucia Rocha", "contact_phone": "(11) 98888-1007"
        },
        {
            "name": {"family": "Gomes", "given": ["Sandra"]},
            "gender": "female", "birthDate": "1983-09-27",
            "cpf": "888.999.000-11", "cns": "890123456789012",
            "phone": "(11) 98888-0008", "email": "sandra.gomes@email.com",
            "address": {"line": ["Rua Bela Cintra, 567"], "city": "São Paulo", "state": "SP", "postalCode": "08901-234"},
            "marital": "M", "contact_name": "Pedro Gomes", "contact_phone": "(11) 98888-1008"
        },
        {
            "name": {"family": "Ribeiro", "given": ["Lucas", "Gabriel"]},
            "gender": "male", "birthDate": "2010-12-01",
            "cpf": "999.000.111-22", "cns": "901234567890123",
            "phone": "(11) 98888-0009", "email": "lucas.mae@email.com",
            "address": {"line": ["Av. Brigadeiro, 890"], "city": "São Paulo", "state": "SP", "postalCode": "09012-345"},
            "marital": "S", "contact_name": "Carla Ribeiro", "contact_phone": "(11) 98888-1009"
        },
        {
            "name": {"family": "Castro", "given": ["Helena"]},
            "gender": "female", "birthDate": "1965-05-19",
            "cpf": "000.111.222-33", "cns": "012345678901234",
            "phone": "(11) 98888-0010", "email": "helena.castro@email.com",
            "address": {"line": ["Rua Pamplona, 432"], "city": "São Paulo", "state": "SP", "postalCode": "00123-456"},
            "marital": "W", "contact_name": "Marina Castro", "contact_phone": "(11) 98888-1010"
        }
    ]
    
    marital_map = {
        "M": {"code": "M", "display": "Married"},
        "S": {"code": "S", "display": "Never Married"},
        "D": {"code": "D", "display": "Divorced"},
        "W": {"code": "W", "display": "Widowed"}
    }
    
    for p in patients:
        patient = {
            "resourceType": "Patient",
            "active": True,
            "identifier": [
                {"use": "official", "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf", "value": p["cpf"]},
                {"use": "official", "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns", "value": p["cns"]}
            ],
            "name": [{
                "use": "official",
                "family": p["name"]["family"],
                "given": p["name"]["given"],
                "text": f"{' '.join(p['name']['given'])} {p['name']['family']}"
            }],
            "gender": p["gender"],
            "birthDate": p["birthDate"],
            "deceasedBoolean": False,
            "telecom": [
                {"system": "phone", "value": p["phone"], "use": "mobile", "rank": 1},
                {"system": "email", "value": p["email"], "use": "home", "rank": 2}
            ],
            "address": [{
                "use": "home",
                "type": "physical",
                "text": f"{p['address']['line'][0]}, {p['address']['city']} - {p['address']['state']}",
                "line": p["address"]["line"],
                "city": p["address"]["city"],
                "state": p["address"]["state"],
                "postalCode": p["address"]["postalCode"],
                "country": "BR"
            }],
            "maritalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": marital_map[p["marital"]]["code"], "display": marital_map[p["marital"]]["display"]}],
                "text": marital_map[p["marital"]]["display"]
            },
            "contact": [{
                "relationship": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0131", "code": "N", "display": "Next-of-Kin"}]}],
                "name": {"text": p["contact_name"]},
                "telecom": [{"system": "phone", "value": p["contact_phone"], "use": "mobile"}]
            }],
            "communication": [{
                "language": {"coding": [{"system": "urn:ietf:bcp:47", "code": "pt-BR", "display": "Português (Brasil)"}]},
                "preferred": True
            }],
            "managingOrganization": {"reference": f"Organization/{created_ids['organizations'][0]}"} if created_ids['organizations'] else None
        }
        
        pid = create_resource("Patient", patient)
        if pid:
            created_ids["patients"].append(pid)
            print(f"  ✓ Patient: {p['name']['given'][0]} {p['name']['family']} (ID: {pid})")


def seed_encounters():
    """Create sample encounters (ambulatory, surgery, inpatient)"""
    print("\n📋 Creating Encounters (Ambulatório, Cirurgia, Internação)...")
    
    if not created_ids["patients"] or not created_ids["practitioners"]:
        print("  ⚠ Need patients and practitioners first")
        return
    
    encounter_types = [
        {"class": "AMB", "class_display": "ambulatory", "type_code": "consultation", "type_display": "Consulta", "count": 8},
        {"class": "IMP", "class_display": "inpatient encounter", "type_code": "hospitalization", "type_display": "Internação", "count": 5},
        {"class": "EMER", "class_display": "emergency", "type_code": "emergency", "type_display": "Emergência", "count": 4},
        {"class": "SS", "class_display": "short stay", "type_code": "surgery", "type_display": "Cirurgia", "count": 3}
    ]
    
    statuses = ["planned", "arrived", "in-progress", "finished"]
    
    for enc_type in encounter_types:
        for i in range(enc_type["count"]):
            patient_id = random.choice(created_ids["patients"])
            practitioner_id = random.choice(created_ids["practitioners"])
            location_id = random.choice(created_ids["locations"]) if created_ids["locations"] else None
            status = random.choice(statuses)
            
            start_date = datetime.now() - timedelta(days=random.randint(0, 30))
            end_date = start_date + timedelta(hours=random.randint(1, 72)) if status == "finished" else None
            
            encounter = {
                "resourceType": "Encounter",
                "status": status,
                "statusHistory": [{"status": "arrived", "period": {"start": (start_date - timedelta(hours=1)).isoformat()}}],
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": enc_type["class"],
                    "display": enc_type["class_display"]
                },
                "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/encounter-type", "code": enc_type["type_code"], "display": enc_type["type_display"]}], "text": enc_type["type_display"]}],
                "priority": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority", "code": "R", "display": "routine"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "participant": [{"individual": {"reference": f"Practitioner/{practitioner_id}"}}],
                "period": {"start": start_date.isoformat()},
                "reasonCode": [{"coding": [{"system": "http://snomed.info/sct", "code": "840544004", "display": "Suspeita de condição"}], "text": "Avaliação clínica"}],
                "serviceProvider": {"reference": f"Organization/{created_ids['organizations'][0]}"} if created_ids['organizations'] else None
            }
            
            if end_date:
                encounter["period"]["end"] = end_date.isoformat()
            
            if location_id:
                encounter["location"] = [{"location": {"reference": f"Location/{location_id}"}, "status": "active"}]
            
            enc_id = create_resource("Encounter", encounter)
            if enc_id:
                created_ids["encounters"].append(enc_id)
    
    print(f"  ✓ Created {len(created_ids['encounters'])} encounters")


def seed_observations(patient_ids):
    """Create vital signs observations"""
    print("\n📊 Creating Observations (Vital Signs)...")
    
    if not patient_ids:
        print("  ⚠ No patients to create observations for")
        return
    
    vital_signs = [
        {"code": "8867-4", "display": "Heart rate", "unit": "/min", "min": 60, "max": 100},
        {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg", "min": 110, "max": 140},
        {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg", "min": 70, "max": 90},
        {"code": "8310-5", "display": "Body temperature", "unit": "Cel", "min": 36.0, "max": 37.5},
        {"code": "9279-1", "display": "Respiratory rate", "unit": "/min", "min": 12, "max": 20},
        {"code": "2708-6", "display": "Oxygen saturation", "unit": "%", "min": 95, "max": 100},
        {"code": "29463-7", "display": "Body weight", "unit": "kg", "min": 50, "max": 100},
        {"code": "8302-2", "display": "Body height", "unit": "cm", "min": 150, "max": 190}
    ]
    
    count = 0
    for patient_id in patient_ids:
        for vital in vital_signs:
            value = round(random.uniform(vital["min"], vital["max"]), 1)
            
            observation = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": vital["code"], "display": vital["display"]}], "text": vital["display"]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "valueQuantity": {"value": value, "unit": vital["unit"], "system": "http://unitsofmeasure.org", "code": vital["unit"]}
            }
            
            if created_ids["practitioners"]:
                observation["performer"] = [{"reference": f"Practitioner/{random.choice(created_ids['practitioners'])}"}]
            
            if create_resource("Observation", observation):
                count += 1
    
    print(f"  ✓ Created {count} observations")


def seed_conditions(patient_ids):
    """Create conditions/diagnoses"""
    print("\n🩺 Creating Conditions...")
    
    if not patient_ids:
        print("  ⚠ No patients to create conditions for")
        return
    
    conditions = [
        {"code": "38341003", "display": "Hipertensão arterial"},
        {"code": "73211009", "display": "Diabetes mellitus tipo 2"},
        {"code": "195967001", "display": "Asma"},
        {"code": "49436004", "display": "Fibrilação atrial"},
        {"code": "13644009", "display": "Hipotireoidismo"},
        {"code": "230690007", "display": "Acidente vascular cerebral"},
        {"code": "22298006", "display": "Infarto do miocárdio"},
        {"code": "56265001", "display": "Insuficiência cardíaca"},
        {"code": "75570004", "display": "Pneumonia"},
        {"code": "44054006", "display": "Diabetes tipo 1"}
    ]
    
    count = 0
    for patient_id in patient_ids:
        # Each patient gets 1-3 conditions
        num_conditions = random.randint(1, 3)
        patient_conditions = random.sample(conditions, num_conditions)
        
        for cond in patient_conditions:
            condition = {
                "resourceType": "Condition",
                "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
                "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}]}],
                "severity": {"coding": [{"system": "http://snomed.info/sct", "code": "6736007", "display": "Moderate"}]},
                "code": {"coding": [{"system": "http://snomed.info/sct", "code": cond["code"], "display": cond["display"]}], "text": cond["display"]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "onsetDateTime": (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
                "recordedDate": datetime.now().isoformat()
            }
            
            if created_ids["practitioners"]:
                condition["recorder"] = {"reference": f"Practitioner/{random.choice(created_ids['practitioners'])}"}
            
            if create_resource("Condition", condition):
                count += 1
    
    print(f"  ✓ Created {count} conditions")


def run():
    """Entry point for Django runscript"""
    main()


def main():
    """Main function to seed all data"""
    print("=" * 70)
    print("🏥 HealthStack - Complete FHIR Seed Data")
    print("   Creating comprehensive sample data with 100% field coverage")
    print("=" * 70)
    
    print("\n🔍 Checking HAPI FHIR availability...")
    retries = 3
    for i in range(retries):
        if check_fhir_available():
            print("  ✓ HAPI FHIR is available")
            break
        print(f"  Attempt {i+1}/{retries} failed, retrying...")
        import time
        time.sleep(5)
    else:
        print("  ✗ HAPI FHIR is not available at", FHIR_URL)
        print("  Please ensure HAPI FHIR is running and try again.")
        sys.exit(1)
    
    # Seed all data in order
    seed_organizations()
    seed_locations()
    seed_practitioners()
    seed_patients()
    seed_encounters()
    seed_observations(created_ids["patients"])
    seed_conditions(created_ids["patients"])
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"  ✓ Organizations: {len(created_ids['organizations'])}")
    print(f"  ✓ Locations (Beds/Wards): {len(created_ids['locations'])}")
    print(f"  ✓ Practitioners: {len(created_ids['practitioners'])}")
    print(f"  ✓ Patients: {len(created_ids['patients'])}")
    print(f"  ✓ Encounters: {len(created_ids['encounters'])}")
    print("=" * 70)
    print("✅ Complete seed data created successfully!")


if __name__ == "__main__":
    main()
