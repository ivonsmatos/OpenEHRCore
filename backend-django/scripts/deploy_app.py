import paramiko
import time
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_command(ssh, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if exit_status != 0:
        print(f"[ERROR] Command failed with status {exit_status}")
        print(err)
        return False
    
    print("[OK]")
    if out:
        print(f"Output:\n{out}")
    return True

def deploy():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("Connected.")
        
        # 1. Create .env file
        print("Creating .env file...")
        # Using provided root password for DB password for simplicity in this context
        env_content = "POSTGRES_USER=postgres\nPOSTGRES_PASSWORD=Protonsysdba@1986"
        run_command(client, f"echo '{env_content}' > /opt/openehrcore/.env")
        
        # 2. Docker Compose Up
        print("Starting containers...")
        # Pointing to the correct docker-compose file relative to project root
        project_dir = "/opt/openehrcore"
        compose_file = "docker/docker-compose.yml"
        
        # Check if file exists
        cmd = f"ls {project_dir}/{compose_file}"
        stdin, stdout, _ = client.exec_command(cmd)
        if stdout.channel.recv_exit_status() != 0:
            print(f"Error: Compose file not found at {project_dir}/{compose_file}")
            # Try to find it? No, fail.
            return

        deploy_cmd = f"cd {project_dir} && docker compose --env-file .env -f {compose_file} up -d --build"
        if not run_command(client, deploy_cmd):
            print("Deploy failed.")
            return

        print("\nDeploy command executed successfully.")
        print("Checking running containers...")
        run_command(client, "docker ps")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
