import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def find_compose():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    cmd = "find /opt/openehrcore -name docker-compose.yml"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    find_compose()
