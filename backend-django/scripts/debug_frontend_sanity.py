import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_sanity():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Check index.html ---")
    _, stdout, stderr = client.exec_command("docker exec openehr_frontend ls -l /usr/share/nginx/html/index.html")
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("\n--- Check Nginx Conf ---")
    _, stdout, stderr = client.exec_command("docker exec openehr_frontend cat /etc/nginx/conf.d/default.conf")
    print("STDOUT:", stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_sanity()
