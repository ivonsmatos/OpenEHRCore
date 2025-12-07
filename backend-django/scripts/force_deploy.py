import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def force_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Forcing deploy of django and frontend...")
    cmd = "cd /opt/openehrcore && docker compose --env-file .env -f docker/docker-compose.yml up -d --build django frontend"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    print("Exit Code:", stdout.channel.recv_exit_status())
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    force_deploy()
