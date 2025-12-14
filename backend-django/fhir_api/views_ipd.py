
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .services.fhir_core import FHIRService
from .auth import KeycloakAuthentication
from rest_framework.permissions import IsAuthenticated
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def list_locations(request):
    """
    List Hierarchy of Locations.
    Returns nested structure: Hospital -> Ward -> Room -> Bed.
    """
    try:
        fhir = FHIRService()
        # Fetch all locations
        resources = fhir.search_resources('Location', {'_count': 200, '_sort': 'name'})
        
        # Build Map by ID
        loc_map = {r['id']: r for r in resources}
        
        # Build Tree
        tree = []
        children_map = {} # parent_id -> [children]
        
        for r in resources:
            r['children'] = []
            # Normalize Operational Status for Frontend
            # FHIR v2-0116: O=Occupied, U=Unoccupied, H=Housekeeping, C=Closed
            # Frontend expects: O=Occupied, U=Free, K=Cleaning, I=Blocked
            op_status = 'U' # Default Unoccupied
            if r.get('operationalStatus'):
                fhir_code = r['operationalStatus'].get('code', 'U')
                # Map FHIR codes to frontend codes
                status_map = {'O': 'O', 'U': 'U', 'H': 'K', 'C': 'I', 'K': 'K', 'I': 'I'}
                op_status = status_map.get(fhir_code, fhir_code)
            r['status_code'] = op_status
            
            part_of = r.get('partOf', {}).get('reference')
            if part_of:
                parent_id = part_of.split('/')[-1]
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(r)
            else:
                # Top level (Hospital)
                tree.append(r)
                
        # Recursive function to attach children
        def attach_children(nodes):
            for node in nodes:
                node_id = node['id']
                if node_id in children_map:
                    node['children'] = children_map[node_id]
                    attach_children(node['children'])
        
        attach_children(tree)
        
        return Response(tree, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_occupancy(request):
    """
    Get Bed Occupancy Stats.
    """
    try:
        fhir = FHIRService()
        # Fetch only Beds
        # Note: physicalType search might need enabling in HAPI.
        # Fallback: Fetch all locations and filter in memory for MVP
        resources = fhir.search_resources('Location', {'_count': 300})
        
        total = 0
        occupied = 0
        cleaning = 0
        free = 0
        
        for r in resources:
            # Check if it is a bed
            is_bed = False
            types = r.get('physicalType', {}).get('coding', [])
            for t in types:
                if t.get('code') == 'bd':
                    is_bed = True
                    break
            
            if is_bed:
                total += 1
                op_status = r.get('operationalStatus', {}).get('code', 'U')
                if op_status == 'O':
                    occupied += 1
                elif op_status in ['H', 'K']:  # Housekeeping/Cleaning
                    cleaning += 1
                elif op_status in ['C', 'I']:  # Closed/Blocked
                    pass  # Will be calculated as total - (occupied + cleaning + free)
                else:
                    free += 1
                    
        return Response({
            "total": total,
            "occupied": occupied,
            "cleaning": cleaning,
            "free": free,
            "occupancy_rate": round((occupied / total * 100), 1) if total > 0 else 0
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error calculating occupancy: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def admit_patient(request):
    """
    Admit patient to a bed.
    Update Location status -> 'O' (Occupied).
    Create Encounter (Inpatient).
    """
    data = request.data
    patient_id = data.get('patient_id')
    location_id = data.get('location_id')
    
    if not patient_id or not location_id:
        return Response({"error": "patient_id and location_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        
        # 1. Update Location Status
        loc_results = fhir.search_resources('Location', {'_id': location_id})
        if not loc_results:
             return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)
        
        location = loc_results[0]
        location['operationalStatus'] = {
             "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
             "code": "O",
             "display": "Occupied"
        }
        
        headers = {'Content-Type': 'application/fhir+json'}
        put_url = f"{fhir.base_url}/Location/{location_id}"
        r_put = requests.put(put_url, json=location, headers=headers)
        if r_put.status_code not in [200, 201]:
             logger.error(f"Failed to update location: {r_put.text}")
             return Response({"error": "Failed to update location status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
        # 2. Create Encounter
        encounter = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter"
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {"start": datetime.utcnow().isoformat() + "Z"},
            "location": [{
                "location": {"reference": f"Location/{location_id}"},
                "status": "active"
            }]
        }
        
        enc_res = fhir.create_resource("Encounter", encounter)
        
        return Response({
            "message": "Admitted successfully",
            "encounter": enc_res,
            "location": location
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error admitting patient: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def get_bed_details(request, location_id):
    """
    Get Bed Details + Current Patient + Clinical Summary.
    """
    try:
        fhir = FHIRService()
        
        # 1. Fetch Location
        loc_results = fhir.search_resources('Location', {'_id': location_id})
        if not loc_results:
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)
        
        location = loc_results[0]
        response_data = {
            "location": location,
            "status_code": location.get('operationalStatus', {}).get('code', 'U'),
            "patient": None,
            "encounter": None,
            "clinical_summary": {
                "conditions": [],
                "observations": [],
                "allergies": []
            }
        }
        
        # 2. If Occupied, Find Active Encounter
        if response_data['status_code'] == 'O':
            # Search Encounter where location.location = Location/<id> AND status=in-progress
            encounters = fhir.search_resources('Encounter', {
                'location': f"Location/{location_id}",
                'status': 'in-progress',
                '_sort': '-date'
            })
            
            if encounters:
                encounter = encounters[0]
                response_data['encounter'] = encounter
                
                # 3. Fetch Patient
                subject_ref = encounter.get('subject', {}).get('reference')
                if subject_ref:
                    patient_id = subject_ref.split('/')[-1]
                    patient = fhir.search_resources('Patient', {'_id': patient_id})
                    if patient:
                        response_data['patient'] = patient[0]
                        
                        # 4. Fetch Clinical Summary (Conditions, Allergies)
                        # Conditions
                        conditions = fhir.search_resources('Condition', {
                            'patient': patient_id,
                            'clinical-status': 'active'
                        })
                        response_data['clinical_summary']['conditions'] = conditions
                        
                        # Observations (Simplified: just last 3)
                        obs = fhir.search_resources('Observation', {
                            'patient': patient_id,
                            '_sort': '-date',
                            '_count': 3
                        })
                        response_data['clinical_summary']['observations'] = obs

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting bed details: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def discharge_patient(request):
    """
    Discharge patient from a bed.
    1. Find active encounter for the location.
    2. Patch Encounter -> status='finished', period.end=now.
    3. Patch Location -> operationalStatus='U' (Unoccupied).
    """
    location_id = request.data.get('location_id')
    
    if not location_id:
        return Response({"error": "location_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        
        # 1. Find active encounter
        encounters = fhir.search_resources('Encounter', {
            'location': f"Location/{location_id}",
            'status': 'in-progress'
        })
        
        if not encounters:
            return Response({"error": "No active encounter found for this location"}, status=status.HTTP_404_NOT_FOUND)
            
        encounter = encounters[0]
        encounter_id = encounter['id']
        
        # 2. Update Encounter (Finish)
        # Using requests directly for PATCH (or PUT)
        
        # Update fields
        encounter['status'] = 'finished'
        if 'period' not in encounter: encounter['period'] = {}
        encounter['period']['end'] = datetime.utcnow().isoformat() + "Z"
        
        headers = {'Content-Type': 'application/fhir+json'}
        put_enc_url = f"{fhir.base_url}/Encounter/{encounter_id}"
        r_enc = requests.put(put_enc_url, json=encounter, headers=headers)
        
        if r_enc.status_code not in [200, 201]:
             logger.error(f"Failed to update encounter: {r_enc.text}")
             return Response({"error": "Failed to update encounter"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
        # 3. Update Location (Dirty/Cleaning)
        # Fetch latest location to be safe
        loc_results = fhir.search_resources('Location', {'_id': location_id})
        if loc_results:
            location = loc_results[0]
            location['operationalStatus'] = {
                 "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
                 "code": "H",
                 "display": "Housekeeping"
            }
            put_loc_url = f"{fhir.base_url}/Location/{location_id}"
            requests.put(put_loc_url, json=location, headers=headers)
            
        return Response({"message": "Discharge successful. Bed marked for cleaning."}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error discharging patient: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def finish_cleaning(request, location_id):
    """
    Mark a bed as cleaned and ready for use.
    Sets Location.operationalStatus -> 'U' (Unoccupied)
    """
    # location_id comes from URL kwarg
    
    if not location_id:
        return Response({"error": "location_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fhir = FHIRService()
        headers = {'Content-Type': 'application/fhir+json'}
        
        # Fetch latest location
        loc_results = fhir.search_resources('Location', {'_id': location_id})
        if not loc_results:
             return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)
             
        location = loc_results[0]
        
        # Update status to U
        location['operationalStatus'] = {
             "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
             "code": "U",
             "display": "Unoccupied"
        }
        
        put_loc_url = f"{fhir.base_url}/Location/{location_id}"
        r = requests.put(put_loc_url, json=location, headers=headers)
        
        if r.status_code not in [200, 201]:
             return Response({"error": "Failed to update location"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
        return Response({"message": "Bed cleaned and ready."}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error finishing cleaning: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([KeycloakAuthentication])
def get_bed_history(request, location_id):
    """
    Retrieve the history of a bed including all encounters that occurred in this location.
    Returns a timeline of patient admissions and discharges.
    """
    fhir = FHIRService()
    
    try:
        # Get the location
        location = fhir.get_resource('Location', location_id)
        if not location:
            return Response({'error': 'Location not found'}, status=404)
        
        # Search for all encounters at this location
        encounters = fhir.search_resources('Encounter', {
            'location': f'Location/{location_id}',
            '_sort': '-date'
        })
        
        history_entries = []
        
        for enc in encounters:
            # Get patient info
            patient_ref = enc.get('subject', {}).get('reference', '')
            patient_id = patient_ref.split('/')[-1] if patient_ref else None
            patient_name = 'Desconhecido'
            
            if patient_id:
                patient = fhir.get_resource('Patient', patient_id)
                if patient and patient.get('name'):
                    name_obj = patient['name'][0]
                    given = ' '.join(name_obj.get('given', []))
                    family = name_obj.get('family', '')
                    patient_name = f"{given} {family}".strip()
            
            # Extract period
            period = enc.get('period', {})
            start = period.get('start', 'N/A')
            end = period.get('end', 'Em andamento')
            
            # Extract status
            enc_status = enc.get('status', 'unknown')
            
            history_entries.append({
                'encounter_id': enc.get('id'),
                'patient_id': patient_id,
                'patient_name': patient_name,
                'admission_date': start,
                'discharge_date': end,
                'status': enc_status,
                'type': 'encounter'
            })
        
        return Response({
            'location_id': location_id,
            'location_name': location.get('name', 'N/A'),
            'current_status': location.get('operationalStatus', {}).get('code', 'U'),
            'history': history_entries,
            'total_encounters': len(history_entries)
        })
        
    except Exception as e:
        logger.error(f"Error fetching bed history: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def transfer_patient(request):
    """
    Stub for Patient Transfer.
    """
    return Response({"error": "Not implemented yet"}, status=status.HTTP_501_NOT_IMPLEMENTED)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def block_bed(request, location_id):
    """
    Stub for Bed Blocking.
    """
    return Response({"error": "Not implemented yet"}, status=status.HTTP_501_NOT_IMPLEMENTED)
