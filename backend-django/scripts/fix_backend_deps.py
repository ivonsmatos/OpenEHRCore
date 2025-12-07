import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def fix_backend_deps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Adding PyJWT to requirements.txt...")
    cmd = "echo 'PyJWT==2.8.0' >> /opt/openehrcore/backend-django/requirements.txt"
    client.exec_command(cmd)
    
    print("Rebuilding Django container...")
    cmd = "cd /opt/openehrcore && docker compose --env-file .env -f docker/docker-compose.yml up -d --build django"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    print("Exit Code:", stdout.channel.recv_exit_status())
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("\nChecking logs again...")
    time.sleep(5) # Wait for start
    _, stdout, stderr = client.exec_command("docker logs openehr_django --tail 20")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    fix_backend_deps()
