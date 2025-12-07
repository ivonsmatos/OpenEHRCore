import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_full_state():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n=== DOCKER PS ===")
    _, stdout, _ = client.exec_command("docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(stdout.read().decode())
    
    print("\n=== FRONTEND LOGS (openehr_frontend) ===")
    _, stdout, _ = client.exec_command("docker logs openehr_frontend --tail 20")
    print(stdout.read().decode())
    
    print("\n=== FRONTEND CONTENT (openehr_frontend) ===")
    _, stdout, stderr = client.exec_command("docker exec openehr_frontend ls -la /usr/share/nginx/html")
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out)
    if err: print("Error listing content:", err)
    
    print("\n=== TEST FRONTEND LOGS (test_frontend) ===")
    _, stdout, _ = client.exec_command("docker logs test_frontend --tail 20")
    print(stdout.read().decode())

    print("\n=== TEST FRONTEND CONTENT (test_frontend) ===")
    _, stdout, stderr = client.exec_command("docker exec test_frontend ls -la /usr/share/nginx/html")
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out)
    if err: print("Error listing content:", err)
    
    client.close()

if __name__ == "__main__":
    debug_full_state()
