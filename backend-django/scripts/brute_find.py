import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def brute_find():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Brute forcing find...")
    cmd = "find /opt/openehrcore/frontend-pwa/src -type f -exec grep -H 'localhost:8000' {} +"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    print("STDOUT:", out)
    print("STDERR:", err)
    
    client.close()

if __name__ == "__main__":
    brute_find()
