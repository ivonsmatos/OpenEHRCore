import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def dump_hook():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    path = "/opt/openehrcore/frontend-pwa/src/hooks/usePatients.ts"
    client.exec_command(f"cat {path} > /tmp/hook_dump.ts")
    time.sleep(1)
    
    # Read all lines via python read() from cat
    # Hopefully small enough (<200 lines) for one read if cat directly, 
    # but paramiko exec_command buffer is the issue.
    # We will read 50 lines at a time.
    
    for i in range(0, 10): # 500 lines limit
        start = i * 50 + 1
        end = (i + 1) * 50
        cmd = f"sed -n '{start},{end}p' /tmp/hook_dump.ts"
        _, stdout, _ = client.exec_command(cmd)
        out = stdout.read().decode()
        if not out.strip(): break
        print(f"--- Chunk {i} ---")
        print(out)

    client.close()

if __name__ == "__main__":
    dump_hook()
