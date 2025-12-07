import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def find_all_loaders():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Searching for loading indicators...")
    # Patterns: 
    # "Carregando"
    # "Loading..."
    # "Spinner"
    # "animate-spin" (Tailwind)
    
    cmd = "grep -rE 'Carregando|Loading|Spinner|animate-spin' /opt/openehrcore/frontend-pwa/src | grep -v 'HeartbeatLoader'"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    if out:
        print("FOUND LOADERS IN:")
        print(out)
    else:
        print("No other loaders found.")
        
    client.close()

if __name__ == "__main__":
    find_all_loaders()
