import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def manual_deploy_v2():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Stopping old frontend instances...")
    client.exec_command("docker rm -f openehr_frontend debug_fg test_frontend")
    
    print("Starting frontend with 'openehrcore_openehr_network'...")
    # Try expected network name
    cmd = "docker run -d --name openehr_frontend --network openehrcore_openehr_network -p 80:80 --restart unless-stopped frontend_debug"
    
    _, stdout, stderr = client.exec_command(cmd)
    cid = stdout.read().decode().strip()
    
    if not cid:
        print("Start failed:", stderr.read().decode())
        # Fallback? No, user should know network name.
        # But let's verify if failing.
    else:
        print(f"Started container {cid}")
        time.sleep(5)
        print("Checking logs (tail 20)...")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 20")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    manual_deploy_v2()
