import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def cat_config():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Reading vite.config.ts...")
    _, stdout, stderr = client.exec_command("cat /opt/openehrcore/frontend-pwa/vite.config.ts")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    cat_config()
