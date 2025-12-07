import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def verify_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Verifying if localhost:8000 still exists...")
    # grep recursive
    # -r = recursive, -l = filenames only
    _, stdout, _ = client.exec_command("grep -r 'localhost:8000' /opt/openehrcore/frontend-pwa/src")
    out = stdout.read().decode().strip()
    
    if out:
        print("ERROR: Found localhost:8000 in:")
        print(out)
    else:
        print("SUCCESS: No occurrences of localhost:8000 found.")
    
    client.close()

if __name__ == "__main__":
    verify_fix()
