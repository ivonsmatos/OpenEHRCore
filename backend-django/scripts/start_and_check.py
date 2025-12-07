import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def start_and_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Starting Docker Frontend...")
    client.exec_command("docker start openehr_frontend")
    time.sleep(3)
    
    print("\n--- Docker PS ---")
    _, stdout, _ = client.exec_command("docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(stdout.read().decode())
    
    print("\n--- Logs ---")
    _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 20")
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())

    print("\n--- Curl ---")
    _, stdout, stderr = client.exec_command("curl -IS http://localhost")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    start_and_check()
