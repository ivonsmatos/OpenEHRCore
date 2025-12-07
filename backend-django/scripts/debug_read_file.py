import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_read_file():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Reading useAuth.tsx...")
    _, stdout, stderr = client.exec_command("cat /opt/openehrcore/frontend-pwa/src/hooks/useAuth.tsx")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_read_file()
