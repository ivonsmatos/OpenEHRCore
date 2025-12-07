import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def list_js_sh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Listing JS files (sh)...")
    cmd = "docker exec openehr_frontend sh -c 'ls /usr/share/nginx/html/assets/*.js'"
    _, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    list_js_sh()
