import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_no_net():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Cleaning up...")
    client.exec_command("docker rm -f openehr_frontend test_no_net debug_fg")
    
    print("Running on default bridge network...")
    cmd = "docker run -d --name openehr_frontend -p 80:80 --restart unless-stopped frontend_debug"
    _, stdout, stderr = client.exec_command(cmd)
    cid = stdout.read().decode().strip()
    
    if not cid:
        print("Run Failed:", stderr.read().decode())
    else:
        print(f"Container ID: {cid}")
        time.sleep(3)
        print("Logs:")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 10")
        print(stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("Curl Check:")
        _, stdout, stderr = client.exec_command("curl -IS http://localhost")
        print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    run_no_net()
