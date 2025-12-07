import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_pkg():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Reading package.json...")
    _, stdout, _ = client.exec_command("cat /opt/openehrcore/frontend-pwa/package.json")
    print(stdout.read().decode())
    
    print("Moving .env.example just in case...")
    client.exec_command("mv /opt/openehrcore/frontend-pwa/.env.example /opt/openehrcore/frontend-pwa/.env.bak")
    
    client.close()

if __name__ == "__main__":
    debug_pkg()
