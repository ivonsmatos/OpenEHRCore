import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_qa_fe():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== FRONTEND QA (Vitest) ===")
    cmd_fe = "docker exec openehr_frontend npm run test -- --run" 
    stdin, stdout, stderr = client.exec_command(cmd_fe)
    
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    run_qa_fe()
