import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def manual_deploy_frontend():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Stopping old frontend...")
    client.exec_command("docker rm -f openehr_frontend")
    client.exec_command("docker rm -f test_frontend") # cleanup test
    
    print("Starting frontend manually using 'frontend_debug' image...")
    # Map port 80:80, network openehr_network
    cmd = "docker run -d --name openehr_frontend --network openehr_network -p 80:80 --restart unless-stopped frontend_debug"
    
    _, stdout, stderr = client.exec_command(cmd)
    cid = stdout.read().decode().strip()
    
    if not cid:
        print("Start failed:", stderr.read().decode())
    else:
        print(f"Started container {cid}")
        time.sleep(5)
        print("Checking logs...")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 20")
        print(stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("\nChecking content...")
        _, stdout, _ = client.exec_command("docker exec openehr_frontend ls /usr/share/nginx/html")
        print("HTML Dir:", stdout.read().decode())
        
    client.close()

if __name__ == "__main__":
    manual_deploy_frontend()
