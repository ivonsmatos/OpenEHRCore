import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_qa_manage():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== BACKEND QA (manage.py test) ===")
    cmd_be = "docker exec openehr_django python manage.py test fhir_api" 
    stdin, stdout, stderr = client.exec_command(cmd_be)
    
    # manage.py writes to stderr mostly?
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    run_qa_manage()
