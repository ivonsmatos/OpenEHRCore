import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_django():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Docker PS -a ---")
    _, stdout, stderr = client.exec_command("docker ps -a")
    print(stdout.read().decode())
    
    print("\n--- Docker Compose File Check ---")
    _, stdout, stderr = client.exec_command("cat /opt/openehrcore/docker/docker-compose.yml")
    print(stdout.read().decode()) # Print first 1000 chars maybe? No, full file to check uncomment.
    
    client.close()

if __name__ == "__main__":
    debug_django()
