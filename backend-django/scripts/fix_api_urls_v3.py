import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def fix_api_urls_v3():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Fixing API URLs with REGEX...")
    
    remote_script = """
import os
import re

ROOT_DIR = '/opt/openehrcore/frontend-pwa/src'
# Regex for: Quote, http://localhost:8000, optional /api/v1, Quote
# We want to replace with: Quote /api/v1 Quote
# Example matches: "http://localhost:8000/api/v1", 'http://localhost:8000/api/v1'

count = 0
for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith('.ts') or file.endswith('.tsx') or file.endswith('.js'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern: (['"])http://localhost:8000(?:/api/v1)?(['"])
            # Group 1: opening quote
            # Group 2: closing quote
            pattern = r"(['\"])http://localhost:8000(?:/api/v1)?(['\"])"
            
            if re.search(pattern, content):
                print(f"Fixing {path}")
                # Replace with: \1/api/v1\2
                # But safer to just force /api/v1 inside quotes if logic matches
                
                new_content = re.sub(pattern, r"\\1/api/v1\\2", content)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1

print(f"Fixed {count} files with Regex.")
"""
    
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/fix_urls_v3.py")
    
    stdin, stdout, stderr = client.exec_command("python3 /tmp/fix_urls_v3.py")
    out = stdout.read().decode()
    print(out)
    if "Fixed 0 files" in out:
        print("WARNING: Even Regex found 0 files. Maybe files are already fixed?")
    
    print("Rebuilding Frontend (NO CACHE)...")
    cmd_build = "docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    
    # wait for build
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        
    if stdout.channel.recv_exit_status() != 0:
        print("Build Failed:", stderr.read().decode())
        return

    print("Restarting Container...")
    client.exec_command("docker restart openehr_frontend")
    
    client.close()

if __name__ == "__main__":
    fix_api_urls_v3()
