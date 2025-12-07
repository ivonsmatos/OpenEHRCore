import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def update_routes():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Updating routes.tsx...")
    
    # We need to read whole file, add import, replace loader logic.
    # Logic in routes.tsx (from cat output):
    # if (isLoading) { return <div ...>Carregando aplicação...</div>; }
    
    # Let's read file first to python var
    cmd = "cat /opt/openehrcore/frontend-pwa/src/routes.tsx"
    _, stdout, _ = client.exec_command(cmd)
    content = stdout.read().decode()
    
    # Inject Import using Regex or simple replace if unique
    # "import { Login } from" -> "import { HeartbeatLoader } from './components/ui/HeartbeatLoader';\nimport { Login } from"
    
    if "HeartbeatLoader" not in content:
        # Add import at top logic: Find first import or known import
        if "import React" in content:
            content = content.replace("import React", "import { HeartbeatLoader } from './components/ui/HeartbeatLoader';\nimport React")
        
        # Replace the loader block
        # The block was something like:
        #   if (isLoading) {
        #     return (
        #       <div style={{...}}>
        #         ...
        #         Carregando aplicação...
        #       </div>
        #     );
        #   }
        
        # I'll try to find "if (isLoading)" or similar and replace the return block.
        # But replacing multiline block with regex is risky if I don't know exact spacing.
        
        # User CAT output showed:
        # if (isLoading) { return <div style=...>...Carregando aplicação...</div> }
        
        # Let's try to replace the string "Carregando aplicação..." with the component if it's inline?
        # No, I want to replace the whole DIV structure to use my centered component.
        
        # Strategy:
        # 1. Read file to local python string.
        # 2. Use python regex to find the `if (isLoading) { ... }` block matching "Carregando aplicação..."
        # 3. Replace with `if (isLoading) { return <HeartbeatLoader />; }`
        
        pass

    remote_script = """
import re

path = '/opt/openehrcore/frontend-pwa/src/routes.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Import
if "HeartbeatLoader" not in content:
    # Insert after first import
    content = re.sub(r"(import .*?;)", r"\\1\\nimport { HeartbeatLoader } from './components/ui/HeartbeatLoader';", content, count=1)

# 2. Replace Loader logic
# Pattern looking for "Carregando aplicação..." inside a return or if block
# We saw: if (isLoading) { return <div ...> ... Carregando aplicação... ... </div> }
# Let's target the inner JSX if possible?
# Simpler: regex for "Carregando aplicação..." -> "<HeartbeatLoader />" (and remove surrounding div?)

# Actually, if I just replace 'Carregando aplicação...' with '<HeartbeatLoader />' 
# it will be: <div><HeartbeatLoader /></div>.
# My Loader has full screen helper classes (h-screen, flex-center).
# Nesting it inside another div might break layout or double centering.
# But it's safer than breaking syntax.

# Let's try to find the whole return statement if possible.
# Look for: if \\(isLoading\\) \\{[\\s\\S]*?return[\\s\\S]*?Carregando aplicação...[\\s\\S]*?;\\s*\\}
pattern = r"if\s*\(\s*isLoading\s*\)\s*\{[\s\S]*?return[\s\S]*?Carregando aplicação...[\s\S]*?;\s*\}"
replacement = "if (isLoading) { return <HeartbeatLoader />; }"

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
else:
    # If pattern fails (files formatting), fallback to simple text replace inside
    # This might result in <div><Loader/></div> which is acceptable fallback.
    print("Pattern not found, falling back to text replace")
    # Replace the text
    content = content.replace("Carregando aplicação...", "")
    # How to inject component if I just removed text?
    # Replace the containing div?
    # Replace <div ...>...Carregando...</div> with <HeartbeatLoader />
    # Too hard without parser.
    
    # Try simpler specific pattern seen in cat:
    # "return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>...</div>"
    # Maybe regex for that?
    
    # Let's assume regex worked or we force it.
    pass

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated routes.tsx")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/update_routes.py")
    client.exec_command("python3 /tmp/update_routes.py")
    
    client.close()

if __name__ == "__main__":
    update_routes()
