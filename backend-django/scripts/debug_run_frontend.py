import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_run_frontend():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Running Test Container ---")
    # Clean up first
    client.exec_command("docker rm -f test_frontend")
    
    cmd = "docker run -d --name test_frontend -p 3000:80 frontend_debug"
    _, stdout, stderr = client.exec_command(cmd)
    container_id = stdout.read().decode().strip()
    print(f"Container ID: {container_id}")
    if not container_id:
        print("Run Failed:", stderr.read().decode())
        return

    time.sleep(5)
    
    print("\n--- Logs ---")
    _, stdout, stderr = client.exec_command("docker logs test_frontend")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("\n--- Status ---")
    _, stdout, _ = client.exec_command("docker ps --filter name=test_frontend")
    print(stdout.read().decode())
    
    # Cleanup if needed, but keeping it for manual check if verified
    # client.exec_command("docker rm -f test_frontend")
    
    client.close()

if __name__ == "__main__":
    debug_run_frontend()
