import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_qa_be():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== BACKEND QA (Pytest) ===")
    cmd_be = "docker exec openehr_django pytest fhir_api/tests" 
    stdin, stdout, stderr = client.exec_command(cmd_be)
    
    # Stream output?
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err: print("BE STDERR:", err)
    
    client.close()

if __name__ == "__main__":
    run_qa_be()
