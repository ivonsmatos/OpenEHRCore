import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def purge_and_rebuild():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Purging Vite cache and dist on HOST...")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/node_modules/.vite")
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/dist")
    
    print("Rebuilding Frontend (Fresh)...")
    cmd_build = "docker build --no-cache -t frontend_debug /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd_build)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        
    if stdout.channel.recv_exit_status() != 0:
        print("Build Failed:", stderr.read().decode())
        return

    print("Restarting Container...")
    client.exec_command("docker restart openehr_frontend")
    
    # Check updated hash?
    # Listing JS again
    print("Checking new JS hash...")
    cmd_ls = "docker exec openehr_frontend sh -c 'ls /usr/share/nginx/html/assets/*.js'"
    _, stdout, _ = client.exec_command(cmd_ls)
    print("New JS Files:", stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    purge_and_rebuild()
