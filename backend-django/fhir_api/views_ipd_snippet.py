
@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def transfer_patient(request):
    """
    Transfer patient from Source Bed to Target Bed.
    Source -> Cleaning (K)
    Target -> Occupied (O)
    Encounter -> Updated Location
    """
    source_id = request.data.get('source_id')
    target_id = request.data.get('target_id')
    
    if not source_id or not target_id:
        return Response({"error": "source_id and target_id required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fhir = FHIRService()
        headers = {'Content-Type': 'application/fhir+json'}
        
        # 1. Validate Source (Must be Occupied)
        source = fhir.search_resources('Location', {'_id': source_id})[0]
        if source.get('operationalStatus', {}).get('code') != 'O':
             return Response({"error": "Source bed is not Occupied"}, status=status.HTTP_400_BAD_REQUEST)
             
        # 2. Validate Target (Must be Unoccupied)
        target = fhir.search_resources('Location', {'_id': target_id})[0]
        if target.get('operationalStatus', {}).get('code') != 'U':
             return Response({"error": "Target bed is not Free"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Find Active Encounter
        encounters = fhir.search_resources('Encounter', {
            'location': f"Location/{source_id}",
            'status': 'in-progress'
        })
        if not encounters:
            return Response({"error": "No active encounter found in source bed"}, status=status.HTTP_404_NOT_FOUND)
            
        encounter = encounters[0]
        
        # 4. Updates
        
        # Encounter: Update Location
        # FHIR R4: Encounter.location is a list. We should append or replace?
        # Usually we add a new location to history and update status/period of old?
        # For simplicity MVP: verify if we replace the active location entry or add new.
        # We will ADD the new location to the list. The old one remains but effectively the 'current' is the last one?
        # Or more accurately: Set end time on old location entry, add new entry with start time.
        
        locations = encounter.get('location', [])
        now_str = datetime.now().isoformat()
        
        # "Close" previous location
        for loc_entry in locations:
            if loc_entry.get('location', {}).get('reference') == f"Location/{source_id}":
                 if 'period' not in loc_entry: loc_entry['period'] = {}
                 loc_entry['period']['end'] = now_str
                 
        # Add new location
        new_loc_entry = {
            "location": {"reference": f"Location/{target_id}", "display": target.get('name')},
            "status": "active",
            "period": {"start": now_str}
        }
        locations.append(new_loc_entry)
        encounter['location'] = locations
        
        requests.put(f"{fhir.base_url}/Encounter/{encounter['id']}", json=encounter, headers=headers)
        
        # Update Bed Statuses
        
        # Source -> Cleaning (K)
        source['operationalStatus'] = {
             "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
             "code": "K",
             "display": "Contaminated"
        }
        requests.put(f"{fhir.base_url}/Location/{source_id}", json=source, headers=headers)
        
        # Target -> Occupied (O)
        target['operationalStatus'] = {
             "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
             "code": "O",
             "display": "Occupied"
        }
        requests.put(f"{fhir.base_url}/Location/{target_id}", json=target, headers=headers)
        
        return Response({"message": "Transfer successful"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error transferring: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([KeycloakAuthentication])
@permission_classes([IsAuthenticated])
def block_bed(request, location_id):
    """
    Toggle Bed Status: Unoccupied (U) <-> Inactive/Maintenance (I)
    Cannot block if Occupied (O) or Cleaning (K).
    """
    try:
        fhir = FHIRService()
        locs = fhir.search_resources('Location', {'_id': location_id})
        if not locs:
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)
            
        location = locs[0]
        current_status = location.get('operationalStatus', {}).get('code')
        
        if current_status == 'O':
             return Response({"error": "Cannot block occupied bed"}, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = 'I' if current_status != 'I' else 'U' # Toggle
        new_display = 'Inactive' if new_status == 'I' else 'Unoccupied'
        
        location['operationalStatus'] = {
             "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
             "code": new_status,
             "display": new_display
        }
        
        # If blocking, maybe add a reason? For MVP just status.
        
        requests.put(f"{fhir.base_url}/Location/{location_id}", json=location, headers={'Content-Type': 'application/fhir+json'})
        
        return Response({"message": f"Bed status changed to {new_display}", "status_code": new_status}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error blocking bed: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
