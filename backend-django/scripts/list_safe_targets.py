import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def list_safe():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Listing targets to file...")
    cmd = "grep -rlE 'Carregando|Loading|Spinner' /opt/openehrcore/frontend-pwa/src/components | grep -v HeartbeatLoader > /tmp/targets.txt"
    client.exec_command(cmd)
    
    print("Reading targets...")
    _, stdout, _ = client.exec_command("cat /tmp/targets.txt")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    list_safe()
