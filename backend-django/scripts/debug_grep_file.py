import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_grep_file():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=10)
    
    print("Grepping useAuth.tsx...")
    _, stdout, stderr = client.exec_command('grep "localhost:8000" /opt/openehrcore/frontend-pwa/src/hooks/useAuth.tsx')
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_grep_file()
