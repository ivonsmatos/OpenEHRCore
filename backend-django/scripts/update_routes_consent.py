import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def update_routes_consent():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    remote_script = """
path = '/opt/openehrcore/frontend-pwa/src/routes.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'ConsentList' not in content:
    # Add imports
    imports = "import ConsentList from './components/consents/ConsentList';\\nimport ConsentForm from './components/consents/ConsentForm';\\n"
    # Insert after last import
    # Look for "import { spacing" which is last one usually
    if "import { spacing" in content:
        content = content.replace("import { spacing", imports + "import { spacing")
    else:
        # Fallback: insert after imports end (harder to detect).
        # Insert at top? No.
        # Just replace "import React" with imports + "import React"? No.
        # Let's insert before "/**" comment.
        if "/**" in content:
            content = content.replace("/**", imports + "\\n/**", 1)
            
    # Add routes
    routes = "                <Route path=\"/consents\" element={<ConsentList />} />\\n                <Route path=\"/consents/new\" element={<ConsentForm />} />\\n"
    
    # Insert before <Route path="*" ...
    if '<Route path="*"' in content:
        content = content.replace('<Route path="*"' , routes + '                <Route path="*"')
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated routes.tsx")
else:
    print("Already updated")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/update_rc.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/update_rc.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    update_routes_consent()
