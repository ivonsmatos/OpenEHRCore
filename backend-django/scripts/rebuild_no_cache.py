import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def rebuild_no_cache():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    cmd = "cd /opt/openehrcore/docker && docker compose build --no-cache django"
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Wait loop
    while not stdout.channel.exit_status_ready():
         if stdout.channel.recv_ready():
             print(stdout.read().decode(), end="")
         time.sleep(2)
             
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    if stdout.channel.recv_exit_status() == 0:
        print("Build Success. Up -d...")
        client.exec_command("cd /opt/openehrcore/docker && docker compose up -d django")
        print("Deployed.")
    else:
        print("Build Failed.")
        
    client.close()

if __name__ == "__main__":
    rebuild_no_cache()
