import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def nuclear_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Running NUCLEAR FIX...")
    
    remote_script = """
import os

ROOT_DIR = '/opt/openehrcore/frontend-pwa'
TARGET = 'localhost:8000'
REPLACE = '45.151.122.234/api/v1' # Or just using relative path if we can manage context
# Safest generic replace for "http://localhost:8000" is "/api/v1" ?
# But if context is "localhost:8000" without http?
# Let's replace 'http://localhost:8000/api/v1' -> '/api/v1'
# And 'http://localhost:8000' -> '/api/v1' (might break if context expects domain)
# But we operate on frontend. Relative path is best.

# Strategy: 
# Replace "http://localhost:8000/api/v1" -> "/api/v1"
# Replace "http://localhost:8000" -> "/api/v1" (DANGEROUS if used for other things? No, port 8000 is backend)

# Let's just track occurrences first.
count = 0
for root, dirs, files in os.walk(ROOT_DIR):
    # Skip node_modules and .git
    if 'node_modules' in dirs: dirs.remove('node_modules')
    if '.git' in dirs: dirs.remove('.git')
    if 'dist' in dirs: dirs.remove('dist') # don't patch dist directly, we rebuild

    for file in files:
        path = os.path.join(root, file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if TARGET in content:
                print(f"NUCLEAR match in: {path}")
                # Analyze context
                # Simple replace
                new_content = content.replace('http://localhost:8000/api/v1', '/api/v1')
                new_content = new_content.replace('http://localhost:8000', '/api/v1') # Fallback
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"FIXED {path}")
                    count += 1
        except UnicodeDecodeError:
            pass # Binary file
        except Exception as e:
            print(f"Error {path}: {e}")

print(f"Nuclear fix applied to {count} files.")
"""
    
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/nuclear_fix.py")
    
    stdin, stdout, stderr = client.exec_command("python3 /tmp/nuclear_fix.py")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("Rebuilding (One last time)...")
    client.exec_command("docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa")
    client.exec_command("docker restart openehr_frontend")
    
    client.close()

if __name__ == "__main__":
    nuclear_fix()
