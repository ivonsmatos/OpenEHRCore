import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def fix_api_urls():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Fixing API URLs in frontend code...")
    
    # Python script to run ON THE SERVER
    remote_script = """
import os

ROOT_DIR = '/opt/openehrcore/frontend-pwa/src'
TARGET = 'http://localhost:8000/api/v1'
REPLACE = '/api/v1'

print(f"Scanning {ROOT_DIR}...")
count = 0
for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if TARGET in content:
                print(f"Fixing {path}")
                new_content = content.replace(TARGET, REPLACE)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1

print(f"Fixed {count} files.")
"""
    
    # Save script to temp file
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/fix_urls.py")
    
    # Run it
    stdin, stdout, stderr = client.exec_command("python3 /tmp/fix_urls.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("Rebuilding Frontend...")
    # Reusing the final deploy process: build image, stop container, run new container
    # But first we need to rebuild the image 'frontend_debug'
    
    print("1. Build...")
    cmd_build = "docker build -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    while not stdout.channel.exit_status_ready():
        pass
    if stdout.channel.recv_exit_status() != 0:
        print("Build Failed:", stderr.read().decode())
        return

    print("2. Restart Container...")
    client.exec_command("docker restart openehr_frontend")
    
    client.close()

if __name__ == "__main__":
    fix_api_urls()
