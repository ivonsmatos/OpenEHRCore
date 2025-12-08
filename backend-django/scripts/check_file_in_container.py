import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_file():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    cmd = "docker exec openehr_django ls -l /app/fhir_api/views_consent.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("Stdout:", stdout.read().decode())
    print("Stderr:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_file()
