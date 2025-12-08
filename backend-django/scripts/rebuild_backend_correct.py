import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def rebuild_django_correct():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Change dir to DOCKER dir and build service 'django'
    cmd = "cd /opt/openehrcore/docker && docker compose build django"
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Non-blocking read loop is better for long builds, but simple for now
    while not stdout.channel.exit_status_ready():
         if stdout.channel.recv_ready():
             print(stdout.read().decode(), end="")
         time.sleep(1)
             
    print(stdout.read().decode())
    print(stderr.read().decode()) # Build errors here
    
    if stdout.channel.recv_exit_status() == 0:
        print("Build Success. Up -d...")
        client.exec_command("cd /opt/openehrcore/docker && docker compose up -d django")
        print("Deployed.")
    else:
        print("Build Failed.")
        
    client.close()

if __name__ == "__main__":
    rebuild_django_correct()
