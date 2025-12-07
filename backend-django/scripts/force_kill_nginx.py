import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def force_kill_nginx():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Force Killing Nginx processes...")
    client.exec_command("killall nginx")
    time.sleep(2)
    
    # Check if anything on port 80
    print("Checking Port 80...")
    _, stdout, _ = client.exec_command("netstat -tulpn | grep :80")
    print(stdout.read().decode())
    
    print("Restarting Docker Frontend...")
    client.exec_command("docker restart openehr_frontend")
    time.sleep(5)
    
    print("Final Curl Check:")
    _, stdout, stderr = client.exec_command("curl -IS http://localhost")
    print(stdout.read().decode())
    
    # Also verify the Docker container logs regarding Port
    print("Docker Logs (tail 5):")
    _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 5")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    force_kill_nginx()
