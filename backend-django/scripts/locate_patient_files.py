import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def locate_patient_files():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Searching for Patient Model...")
    # Looking for 'class Patient' to find models.py or similar
    cmd = 'grep -r "class Patient" /opt/openehrcore/backend-django'
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    print("\nSearching for Patient View...")
    # Looking for ViewSet or similar
    cmd = 'grep -r "Patient" /opt/openehrcore/backend-django/fhir_api | grep "class" | grep -v "Serializer"'
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    locate_patient_files()
