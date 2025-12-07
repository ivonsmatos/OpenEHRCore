import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_read_safe():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=10)
    
    remote_script = """
import sys
try:
    with open('/opt/openehrcore/frontend-pwa/src/hooks/useAuth.tsx', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            # Read a larger chunk to be sure we find it
            if 40 <= i <= 70:
                print(f"{i}: {line.rstrip()}")
except Exception as e:
    print(e)
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/read_safe.py")
    
    print("Reading safe lines...")
    _, stdout, stderr = client.exec_command("python3 /tmp/read_safe.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_read_safe()
