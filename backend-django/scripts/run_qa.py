import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_qa():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== BACKEND QA (Pytest) ===")
    # Running pytest with -v and specific path to avoid long collection
    cmd_be = "docker exec openehr_django pytest fhir_api/tests" 
    stdin, stdout, stderr = client.exec_command(cmd_be)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err: print("BE STDERR:", err)
    
    print("\n=== FRONTEND QA (Vitest) ===")
    # npm run test (vitest run)
    cmd_fe = "docker exec openehr_frontend npm run test -- --run" 
    stdin, stdout, stderr = client.exec_command(cmd_fe)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err: print("FE STDERR:", err)
    
    client.close()

if __name__ == "__main__":
    run_qa()
