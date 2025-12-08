import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_consent():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    cmd = "grep -r 'class Consent' /opt/openehrcore/backend-django"
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_consent()
