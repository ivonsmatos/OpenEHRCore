import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def fix_api_urls_v2():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Fixing DOUBLE QUOTED API URLs in frontend code...")
    
    # Python script to run ON THE SERVER
    remote_script = """
import os

ROOT_DIR = '/opt/openehrcore/frontend-pwa/src'
TARGET_SINGLE = "'http://localhost:8000/api/v1'"
TARGET_DOUBLE = '"http://localhost:8000/api/v1"'
REPLACE_SINGLE = "'/api/v1'"
REPLACE_DOUBLE = '"/api/v1"'

print(f"Scanning {ROOT_DIR} for leftovers...")
count = 0
for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx') or file.endswith('.js'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            if TARGET_DOUBLE in content:
                print(f"Fixing DOUBLE quotes in {path}")
                content = content.replace(TARGET_DOUBLE, REPLACE_DOUBLE)
                modified = True
            
            if TARGET_SINGLE in content:
                print(f"Fixing SINGLE quotes in {path}")
                content = content.replace(TARGET_SINGLE, REPLACE_SINGLE)
                modified = True
            
            # Catch mixed cases or variations if possible? No, stick to exact provided.
            
            if modified:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1

print(f"Fixed {count} files.")
"""
    
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/fix_urls_v2.py")
    
    stdin, stdout, stderr = client.exec_command("python3 /tmp/fix_urls_v2.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("Checking for any .env file...")
    _, stdout, stderr = client.exec_command("ls -la /opt/openehrcore/frontend-pwa/.env")
    print(stdout.read().decode())
    
    print("\nRebuilding Frontend...")
    cmd_build = "docker build -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    if stdout.channel.recv_exit_status() != 0:
        print("Build Failed:", stderr.read().decode())
        return

    print("Restarting Container...")
    client.exec_command("docker restart openehr_frontend")
    
    client.close()

if __name__ == "__main__":
    import time
    fix_api_urls_v2()
