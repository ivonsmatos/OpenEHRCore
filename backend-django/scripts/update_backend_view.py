import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def update_view():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # We will append the new function instead of replacing, 
    # and update urls.py to point to it, OR replace create_patient logic if we can target it.
    
    # Replacing is better to keep urls clean.
    # Logic:
    # @api_view(['GET', 'POST'])
    # def patients_endpoint(request):
    #   if request.method == 'POST': ... (old logic)
    #   if request.method == 'GET': ... (search logic)
    
    # However, replacing a block purely with regex blind is risky if indent varies.
    # But Views usually have standard structure.
    
    # Strategy: Read file, find "def create_patient", replace until return.
    # Or Append "def list_patients" and update urls.py. This is safer (less breakage risk).
    
    print("Appending list_patients to views.py...")
    
    new_function = """

@api_view(['GET'])
def list_patients(request):
    \"\"\"
    Lista pacientes com filtros.
    GET /api/v1/patients/list/
    Params: name, cpf, gender, birthdate
    \"\"\"
    try:
        fhir_service = FHIRService()
        
        # Build search dict
        search_params = {}
        
        # Name (contains)
        name = request.query_params.get('name')
        if name:
            search_params['name'] = name
            
        # CPF (identifier)
        cpf = request.query_params.get('cpf')
        if cpf:
            # FHIR identifier search: system|value
            # But HAPI/FHIR helper might handle raw value if configured.
            # Assuming basic search for now.
            search_params['identifier'] = cpf 
            
        # Exact params
        for field in ['gender', 'birthdate', 'email']:
             val = request.query_params.get(field)
             if val: search_params[field] = val
             
        # Pagination
        # FHIR uses _count and _offset usually.
        # request.query_params might have 'page'
        
        results = fhir_service.search_resources('Patient', search_params)
        
        # Manual pagination or FHIR bundle handling?
        # fhir_service returns List[Dict].
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
    
    # Append to file
    escape_code = new_function.replace('"', '\\"') # minimal escape
    remote_script = f"""
with open('/opt/openehrcore/backend-django/fhir_api/views.py', 'a', encoding='utf-8') as f:
    f.write({repr(new_function)})
print("Appended list_patients")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/append_view.py")
    client.exec_command("python3 /tmp/append_view.py")
    
    client.close()

if __name__ == "__main__":
    update_view()
