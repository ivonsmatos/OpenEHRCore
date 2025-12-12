
import os
import sys
import django
from fhir_api.services.fhir_core import FHIRService

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

def seed_locations():
    fhir = FHIRService()
    print("--- Seeding Hospital Structure ---")
    
    # 1. Hospital (Building)
    hospital = {
        "resourceType": "Location",
        "status": "active",
        "name": "Hospital Geral OpenEHR",
        "mode": "instance",
        "physicalType": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "bu",
                "display": "Building"
            }]
        }
    }
    h_res = fhir.create_resource("Location", hospital)
    h_id = h_res.get('id')
    print(f"Created Hospital: {h_res.get('name')} (ID: {h_id})")

    # 2. Wards (Alas)
    wards = [
        {"name": "Internação Geral (Ala Norte)", "code": "WARD-N"},
        {"name": "UTI Adulto", "code": "ICU-A"}
    ]
    
    for w in wards:
        ward_res = {
            "resourceType": "Location",
            "status": "active",
            "name": w['name'],
            "mode": "instance",
            "physicalType": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                    "code": "wi",
                    "display": "Wing"
                }]
            },
            "partOf": {"reference": f"Location/{h_id}"}
        }
        w_created = fhir.create_resource("Location", ward_res)
        w_id = w_created.get('id')
        print(f"  Created Ward: {w['name']} (ID: {w_id})")
        
        # 3. Rooms & Beds per Ward
        if w['code'] == "WARD-N":
            # Create 3 Rooms with 2 Beds each
            for r_num in range(101, 104):
                room_res = {
                    "resourceType": "Location",
                    "status": "active",
                    "name": f"Quarto {r_num}",
                    "physicalType": {"coding": [{"code": "ro", "display": "Room"}]},
                    "partOf": {"reference": f"Location/{w_id}"}
                }
                r_created = fhir.create_resource("Location", room_res)
                r_id = r_created.get('id')
                print(f"    Created Room: Quarto {r_num}")
                
                for b_letter in ['A', 'B']:
                    bed_res = {
                        "resourceType": "Location",
                        "status": "active",
                        "name": f"Leito {r_num}-{b_letter}",
                        "description": "Leito Standard",
                        "physicalType": {"coding": [{"code": "bd", "display": "Bed"}]},
                        "partOf": {"reference": f"Location/{r_id}"},
                        # Operational Status (CodeSystem generic)
                        "operationalStatus": {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                            "code": "U", # Unoccupied
                            "display": "Unoccupied"
                        }
                    }
                    b_created = fhir.create_resource("Location", bed_res)
                    print(f"      Created Bed: {bed_res['name']}")
                    
        elif w['code'] == "ICU-A":
             # Create 5 Boxes (Directly Beds or Room=Box)
             for i in range(1, 6):
                bed_res = {
                        "resourceType": "Location",
                        "status": "active",
                        "name": f"Leito UTI-{i}",
                        "description": "Leito Intensivo",
                        "physicalType": {"coding": [{"code": "bd", "display": "Bed"}]},
                        "partOf": {"reference": f"Location/{w_id}"},
                        "operationalStatus": {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                            "code": "U",
                            "display": "Unoccupied"
                        }
                 }
                fhir.create_resource("Location", bed_res)
                print(f"    Created ICU Bed: Leito UTI-{i}")

if __name__ == "__main__":
    seed_locations()
