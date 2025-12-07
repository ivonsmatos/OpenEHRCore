import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_all():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Grepping matches in ALL files...")
    # exclude node_modules and .git
    cmd = "grep -r 'localhost:8000' /opt/openehrcore/frontend-pwa --exclude-dir=node_modules --exclude-dir=.git"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    if out:
        print("FOUND MATCHES:")
        print(out)
    else:
        print("No matches in source/config files.")
        
    client.close()

if __name__ == "__main__":
    check_all()
