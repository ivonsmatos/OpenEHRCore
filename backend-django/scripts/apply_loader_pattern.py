import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def apply_pattern():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Applying Loader Pattern...")
    
    remote_script = """
import os
import re

ROOT = '/opt/openehrcore/frontend-pwa/src/components'

def get_import_path(file_path):
    target_dir = '/opt/openehrcore/frontend-pwa/src/components/ui'
    file_dir = os.path.dirname(file_path)
    rel = os.path.relpath(target_dir, file_dir)
    return rel.replace(os.sep, '/') + '/HeartbeatLoader'

count = 0 
for root, dirs, files in os.walk(ROOT):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (IOError, UnicodeDecodeError) as e:
                print(f"Skipping {path}: {str(e)}")
                continue
            
            # Use regex to find block: if (loading) return <div...>...</div>;
            regex_capture = r"(if\s*\(\s*(?:loading|isLoading)\s*\)\s*return\s*)<div[^>]*>[\s\S]*?<\/div>;"
            
            if re.search(regex_capture, content):
                print(f"Patching {path}")
                
                def repl(m):
                    prefix = m.group(1)
                    return f"{prefix}<HeartbeatLoader fullScreen={{False}} />;"
                
                new_content = re.sub(regex_capture, repl, content)
                
                # Logic for React Import / Component import
                if "HeartbeatLoader" not in new_content:
                    imp_path = get_import_path(path)
                    if not imp_path.startswith('.'): imp_path = './' + imp_path
                    
                    # Insert import after the last import or specific one
                    # Find first import
                    match_imp = re.search(r"import .*?;", new_content)
                    if match_imp:
                         new_content = re.sub(r"(import .*?;)", f"\\\\1\\nimport {{ HeartbeatLoader }} from '{imp_path}';", new_content, count=1)
                    else:
                         new_content = f"import {{ HeartbeatLoader }} from '{imp_path}';\\n" + new_content

                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1

print(f"Patched {count} files.")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/apply_loader.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/apply_loader.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("Rebuilding (Fresh)...")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/dist")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/node_modules/.vite")
    cmd_build = "docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    
    start = time.time()
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        if time.time() - start > 600:
            print("Timeout")
            break
            
    if stdout.channel.recv_exit_status() == 0:
        print("Success.")
        client.exec_command("docker restart openehr_frontend")
    else:
        print("Fail:", stderr.read().decode())
        
    client.close()

if __name__ == "__main__":
    apply_pattern()
