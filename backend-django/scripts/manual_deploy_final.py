import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def manual_deploy_final():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Stopping old containers...")
    client.exec_command("docker rm -f openehr_frontend debug_fg test_frontend test_no_net")
    
    print("Starting Frontend on 'docker_openehr_network'...")
    cmd = "docker run -d --name openehr_frontend --network docker_openehr_network -p 80:80 --restart unless-stopped frontend_debug"
    
    _, stdout, stderr = client.exec_command(cmd)
    cid = stdout.read().decode().strip()
    
    if not cid:
        print("Start Failed:", stderr.read().decode())
    else:
        print(f"Container ID: {cid}")
        time.sleep(5)
        print("Logs:")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 10")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("Curl Check:")
        _, stdout, stderr = client.exec_command("curl -IS http://localhost")
        print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    manual_deploy_final()
