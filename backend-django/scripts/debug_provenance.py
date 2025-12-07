import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_provenance():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Creating provenance_test.txt in src...")
    client.exec_command("touch /opt/openehrcore/frontend-pwa/src/provenance_test.txt")
    
    print("Rebuilding...")
    cmd_build = "docker build -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        
    print("Restarting...")
    client.exec_command("docker restart openehr_frontend")
    
    print("Checking for provenance file in container...")
    # It won't be in /usr/share/nginx/html unless configured to copy assets?
    # Wait, vite build bundles everything. It doesn't copy random txt files from src unless imported.
    # Ah.
    
    # Better: Create a file in 'public'.
    # Files in 'public' are copied to root dist.
    
    print("Creating provenance_test.txt in public...")
    client.exec_command("touch /opt/openehrcore/frontend-pwa/public/provenance_test.txt")
    
    # Rebuild again?
    # Let's assume the previous build failed to pick it up because I put it in src.
    
    print("Rebuilding (AGAIN with public file)...")
    cmd_build = "docker build -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    while not stdout.channel.exit_status_ready():
        time.sleep(2)

    print("Restarting...")
    client.exec_command("docker restart openehr_frontend")
    
    print("Checking for file in container root...")
    _, stdout, _ = client.exec_command("docker exec openehr_frontend ls /usr/share/nginx/html/provenance_test.txt")
    out = stdout.read().decode().strip()
    
    if "provenance_test.txt" in out:
        print("SUCCESS: Build context is CORRECT.")
    else:
        print("FAILURE: provenance_test.txt NOT FOUND in container.")
        
    client.close()

if __name__ == "__main__":
    debug_provenance()
