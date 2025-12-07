import paramiko
import time
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_command(ssh, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Live output streaming could be implemented, but simple wait is safer for script
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
        print(f"Output: {out[:200]}...") # Truncate long output
    return True

def setup_server():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("Connected.")
        
        # 1. Update System
        if not run_command(client, "apt-get update"): return
        
        # 2. Install Deps
        if not run_command(client, "apt-get install -y curl git htop"): return
        
        # 3. Check/Install Docker
        print("Checking Docker...")
        stdin, stdout, _ = client.exec_command("docker --version")
        if stdout.channel.recv_exit_status() != 0:
            print("Installing Docker...")
            if not run_command(client, "curl -fsSL https://get.docker.com | sh"): 
                print("Failed to install Docker")
                return
        else:
            print("Docker already installed.")
            
        # 4. Create Project Directory
        run_command(client, "mkdir -p /opt/openehrcore")

        # 5. Git Setup
        print("\nConfiguring Git Repo...")
        repo_url = "https://github.com/ivonsmatos/OpenEHRCore.git"
        project_dir = "/opt/openehrcore"
        
        # Check contents
        stdin, stdout, _ = client.exec_command(f"ls -A {project_dir}")
        contents = stdout.read().decode().strip()
        
        if not contents:
             print(f"Cloning {repo_url}...")
             if not run_command(client, f"git clone {repo_url} {project_dir}"): 
                 print("Failed to clone. Repository might be private or URL incorrect.")
                 return
        else:
             print(f"Directory {project_dir} not empty. Attempting git pull...")
             # Check if git repo
             stdin, stdout, _ = client.exec_command(f"cd {project_dir} && git rev-parse --is-inside-work-tree")
             if stdout.channel.recv_exit_status() == 0:
                 run_command(client, f"cd {project_dir} && git pull")
             else:
                 print(f"WARNING: {project_dir} contains files but is not a git repo. Manual intervention required.")
        
        print("\nServer Setup Complete.")
        
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    setup_server()
