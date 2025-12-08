import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_endpoint():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Try local curl inside the server
    cmd = "curl -v http://localhost:8000/api/v1/consents/list/"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_endpoint()
