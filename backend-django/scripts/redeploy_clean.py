import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def redeploy_clean():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Stopping containers...")
    stdin, stdout, stderr = client.exec_command("cd /opt/openehrcore && docker compose -f docker/docker-compose.yml down")
    stdout.channel.recv_exit_status()
    print("Down complete.")
    
    print("Pruning Docker system to free ports/resources...")
    client.exec_command("docker system prune -f")
    
    print("Redeploying Full Stack...")
    cmd = "cd /opt/openehrcore && docker compose --env-file .env -f docker/docker-compose.yml up -d --build"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    if stdout.channel.recv_exit_status() != 0:
        print("Deploy Failed:")
        print(stderr.read().decode())
    else:
        print("Deploy Successful!")
        print(stdout.read().decode())
        
    print("\nCheck containers:")
    _, stdout, _ = client.exec_command("docker ps")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    redeploy_clean()
