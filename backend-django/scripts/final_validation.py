import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def final_validation():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Final Validation ---")
    print("1. Checking curl localhost:")
    _, stdout, stderr = client.exec_command("curl -IS http://localhost")
    print(stdout.read().decode())
    
    print("2. Checking Docker PS:")
    _, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}} {{.Status}} {{.Ports}}'")
    print(stdout.read().decode())
    
    print("3. Checking Nginx Logs (Last 10):")
    _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 10")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    final_validation()
