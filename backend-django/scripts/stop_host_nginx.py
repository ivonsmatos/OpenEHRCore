import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def stop_host_nginx():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Checking Host Nginx Status...")
    _, stdout, stderr = client.exec_command("systemctl status nginx")
    print(stdout.read().decode())
    
    print("Stopping Host Nginx...")
    client.exec_command("systemctl stop nginx")
    client.exec_command("systemctl disable nginx")
    
    time.sleep(2)
    
    print("Restarting Docker Frontend to ensure bind...")
    client.exec_command("docker restart openehr_frontend")
    time.sleep(5)
    
    print("Final Curl Check:")
    _, stdout, stderr = client.exec_command("curl -IS http://localhost")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    stop_host_nginx()
