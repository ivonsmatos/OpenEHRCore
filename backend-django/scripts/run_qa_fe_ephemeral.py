import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_qa_fe_ephemeral():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== FRONTEND QA (Vitest - Ephemeral) ===")
    # npm install might be needed if binaries are missing?
    # Assuming node_modules is intact.
    # Also npx vitest might be better.
    
    cmd_fe = "docker run --rm -v /opt/openehrcore/frontend-pwa:/app -w /app node:18-alpine npm run test -- --run" 
    stdin, stdout, stderr = client.exec_command(cmd_fe)
    
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    run_qa_fe_ephemeral()
