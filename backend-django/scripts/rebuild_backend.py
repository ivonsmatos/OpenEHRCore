import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def rebuild_django():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Change dir and build
    cmd = "cd /opt/openehrcore/backend-django && docker compose build openehr_django"
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Wait loop
    exit_status = stdout.channel.recv_exit_status() # Blocking wait
    
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    if exit_status == 0:
        print("Build Success. Up -d...")
        client.exec_command("cd /opt/openehrcore/backend-django && docker compose up -d openehr_django")
        print("Deployed.")
    else:
        print("Build Failed.")
        
    client.close()

if __name__ == "__main__":
    rebuild_django()
