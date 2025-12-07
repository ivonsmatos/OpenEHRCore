import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_run_fg():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Check Django Status ---")
    _, stdout, _ = client.exec_command("docker ps -a | grep django")
    print(stdout.read().decode())
    
    print("\n--- Running Frontend Foreground ---")
    client.exec_command("docker rm -f openehr_frontend test_frontend debug_fg")
    
    # Run in foreground, wait 5s then close channel? 
    # Use timeout on exec_command? Paramiko exec_command is non-blocking.
    # We read from stdout until EOF or timeout.
    
    cmd = "docker run --rm --name debug_fg --network openehr_network -p 80:80 frontend_debug"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    
    # Read output
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    print("STDOUT:", out)
    print("STDERR:", err)
    
    client.close()

if __name__ == "__main__":
    debug_run_fg()
