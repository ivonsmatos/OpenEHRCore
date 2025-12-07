import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def read_files():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Define files
    files = [
        "/opt/openehrcore/backend-django/fhir_api/services/fhir_core.py",
        "/opt/openehrcore/backend-django/fhir_api/views.py"
    ]
    
    for f in files:
        print(f"=== {f} ===")
        # Read lines 1-150
        cmd = f"head -n 150 {f}"
        _, stdout, _ = client.exec_command(cmd)
        out = stdout.read().decode()
        # Clean lines to avoid buffer confusing
        print(out[:2000] + "\n... (truncated if long)") 
    
    client.close()

if __name__ == "__main__":
    read_files()
