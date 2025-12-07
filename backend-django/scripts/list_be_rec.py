import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def list_be_rec():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # maxdepth 4 should cover apps
    cmd = "find /opt/openehrcore/backend-django -maxdepth 4 -not -path '*/.*' -not -path '*/__pycache__*'"
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    list_be_rec()
