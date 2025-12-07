import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def replace_loaders():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Running Mass Loader Replacer...")
    
    remote_script = """
import os
import re

ROOT_DIR = '/opt/openehrcore/frontend-pwa/src/components'
# Explicitly include specific files if outside components
ADDITIONAL_FILES = ['/opt/openehrcore/frontend-pwa/src/routes.tsx'] 

# Regex strategies
# 1. Simple text "Carregando..." inside a div -> <HeartbeatLoader fullScreen={false} />
#    This covers: <div>Carregando...</div>
#    And: <div className="...">Carregando...</div>
# 2. "Loading..." -> same.

count = 0

def process_file(path):
    global count
    modified = False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    # Check matches
    if "HeartbeatLoader" in content and "import" in content and "routes.tsx" not in path:
        # Already has loader import? maybe manual fix?
        # Continue to replace if old stuff persists
        pass
        
    original_content = content
    
    # 1. Inject Import if needed (and if we are about to modify)
    # We delay injection until we confirm modification, OR we inject aggressively (safe-ish).
    # Lets check for targets first.
    targets = ["Carregando...", "Loading...", "Spinner"]
    has_target = any(t in content for t in targets)
    
    if not has_target:
        return

    # Regex for <div>...Carregando...</div>
    # <div[^>]*>\s*Carregando\.\.\.\s*<\/div>
    # Replaces entire DIV.
    
    # Also "Carregando pacientes..." etc.
    # Carregando [a-zA-Z]+...
    
    regex_div = r"<div[^>]*>\s*(Carregando|Loading)[^<]*?\.{3}\s*<\/div>"
    replacement = "<HeartbeatLoader fullScreen={false} label='Carregando...' />"
    
    if re.search(regex_div, content):
        content = re.sub(regex_div, replacement, content)
        modified = True
    
    # Also replace bare text "Carregando..." if inside parens? 
    # e.g. return <div>Carregando...</div> -> return <div><HeartbeatLoader.../></div>.
    # regex matches the div.
    
    # Handle "Spinner" component usage
    regex_spinner = r"<Spinner[^>]*\/>"
    if re.search(regex_spinner, content):
        content = re.sub(regex_spinner, replacement, content)
        modified = True

    if modified:
        # Add import
        if "HeartbeatLoader" not in content:
             # Find relative path to components/ui/HeartbeatLoader
             # Assuming we are in src/components/XYZ
             # Hard to calc relative path in simple script without path logic.
             # Easier: use Absolute import alias '@/' if configured? 
             # Vite usually supports aliases. But lets try relative if possible.
             # Or assume '@components/ui/HeartbeatLoader'.
             # Let's check tsconfig? No time.
             # Let's use relative based on depth?
             
             # Hack: In src/components roots it is './ui/HeartbeatLoader'
             # In src/components/subdir it is '../../components/ui/HeartbeatLoader' ?? No 'ui' is in components.
             # src/components/ui/HeartbeatLoader.tsx
             
             # FROM src/components/PatientList.tsx -> './ui/HeartbeatLoader'
             # FROM src/components/patients/X.tsx -> '../ui/HeartbeatLoader'
             
             # Let's compute depth relative to components
             rel_path = os.path.relpath('/opt/openehrcore/frontend-pwa/src/components/ui/HeartbeatLoader', os.path.dirname(path))
             # remove extension
             import_path = rel_path
             
             # import { HeartbeatLoader } from '...';
             import_stmt = f"import {{ HeartbeatLoader }} from '{import_path}';"
             
             content = re.sub(r"(import .*?;)", f"\\\\1\\n{import_stmt}", content, count=1)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {path}")
        count += 1

# Walk
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
    
    # Rebuild
    print("Purge & Rebuild...")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/node_modules/.vite")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/dist")
    cmd_build = "docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        
    print("Restarting...")
    client.exec_command("docker restart openehr_frontend")
    
    client.close()

if __name__ == "__main__":
    replace_loaders()
