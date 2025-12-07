import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def read_view_next():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    cmd = "sed -n '110,160p' /opt/openehrcore/backend-django/fhir_api/views.py"
    _, stdout, _ = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    read_view_next()
