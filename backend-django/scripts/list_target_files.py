import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def list_targets():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Listing files...")
    cmd = "grep -rlE 'Carregando|Loading|Spinner' /opt/openehrcore/frontend-pwa/src | grep -v HeartbeatLoader"
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    list_targets()
