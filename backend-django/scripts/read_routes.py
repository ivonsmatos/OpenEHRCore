import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def read_routes():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Reading routes.tsx...")
    _, stdout, _ = client.exec_command("cat /opt/openehrcore/frontend-pwa/src/routes.tsx")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    read_routes()
