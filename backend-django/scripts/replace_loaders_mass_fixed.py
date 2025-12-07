import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def replace_loaders_fixed():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Running Mass Loader Replacer (Fixed)...")
    
    remote_script = """
import os
import re

ROOT_DIR = '/opt/openehrcore/frontend-pwa/src/components'

count = 0

def process_file(path):
    global count
    modified = False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    targets = ["Carregando...", "Loading...", "Spinner"]
    has_target = any(t in content for t in targets)
    
    if not has_target:
        return

    regex_div = r"<div[^>]*>\s*(Carregando|Loading)[^<]*?\.{3}\s*<\/div>"
    replacement = "<HeartbeatLoader fullScreen={false} label='Carregando...' />"
    
    if re.search(regex_div, content):
        content = re.sub(regex_div, replacement, content)
        modified = True
    
    regex_spinner = r"<Spinner[^>]*\/>"
    if re.search(regex_spinner, content):
        content = re.sub(regex_spinner, replacement, content)
        modified = True

    if modified:
        if "HeartbeatLoader" not in content:
             rel_path = os.path.relpath('/opt/openehrcore/frontend-pwa/src/components/ui/HeartbeatLoader', os.path.dirname(path))
             import_path = rel_path.replace(os.sep, '/')
             if not import_path.startswith('.'):
                 import_path = './' + import_path
             
             import_stmt = f"import {{ HeartbeatLoader }} from '{import_path}';"
             content = re.sub(r"(import .*?;)", f"\\\\1\\n{import_stmt}", content, count=1)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {path}")
        count += 1

for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            process_file(os.path.join(root, file))

print(f"Total files patched: {count}")
"""
    
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/mass_loader.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/mass_loader.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("Purge & Rebuild...")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/node_modules/.vite")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/dist")
    cmd_build = "docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    
    start = time.time()
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        if time.time() - start > 600: # 10 min timeout
            print("Build Timeout!")
            break
        
    if stdout.channel.recv_exit_status() == 0:
        print("Build Success.")
        print("Restarting...")
        client.exec_command("docker restart openehr_frontend")
    else:
        print("Build Failed:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    replace_loaders_fixed()
