import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def analyze_search():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Reading PatientList.tsx...")
    # Guess path: src/components/PatientList.tsx or src/components/patient/PatientList.tsx ?
    # Step 9513 showed PatientList.tsx in src/components root.
    
    cmd = "cat /opt/openehrcore/frontend-pwa/src/components/PatientList.tsx"
    _, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    # Also check Backend View for Patient
    print("\nReading Backend Patient View...")
    # Guess: backend-django/fhir_api/views_patient.py
    cmd_be = "cat /opt/openehrcore/backend-django/fhir_api/views_patient.py"
    _, stdout, _ = client.exec_command(cmd_be)
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    analyze_search()
