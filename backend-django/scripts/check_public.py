import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_public():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Grepping public folder...")
    cmd = "grep -r 'localhost:8000' /opt/openehrcore/frontend-pwa/public"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    if out:
        print("FOUND IN PUBLIC:")
        print(out)
    else:
        print("Not found in public.")
        
    client.close()

if __name__ == "__main__":
    check_public()
