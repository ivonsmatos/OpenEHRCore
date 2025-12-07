import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_final():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Processes (nginx) ---")
    _, stdout, _ = client.exec_command("ps aux | grep nginx")
    print(stdout.read().decode())
    
    print("\n--- Docker PS ---")
    _, stdout, _ = client.exec_command("docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(stdout.read().decode())
    
    print("\n--- Curl Verbose ---")
    _, stdout, stderr = client.exec_command("curl -v http://localhost")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_final()
