import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def find_loader():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Searching for loader text...")
    cmd = "grep -r 'Carregando aplicação...' /opt/openehrcore/frontend-pwa/src"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    if out:
        print("FOUND:", out)
    else:
        print("Not found text. Searching for 'Loading' component usage...")
        client.exec_command("find /opt/openehrcore/frontend-pwa/src -name '*Loading*' -o -name '*Spinner*'")
        
    client.close()

if __name__ == "__main__":
    find_loader()
