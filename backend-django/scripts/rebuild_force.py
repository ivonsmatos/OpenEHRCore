import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def rebuild_fe():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Rebuilding Frontend...")
    # Clean vite cache again just in case
    client.exec_command("rm -rf /opt/openehrcore/frontend-pwa/node_modules/.vite")
    
    cmd = "docker build --no-cache -t frontend_search /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    start = time.time()
    while not stdout.channel.exit_status_ready():
        time.sleep(2)
        if time.time() - start > 600:
             print("Timeout")
             break
             
    if stdout.channel.recv_exit_status() == 0:
         print("Build Success.")
         print("Restarting container...")
         client.exec_command("docker restart openehr_frontend")
    else:
         print("Build Failed:")
         print(stderr.read().decode())
         
    client.close()

if __name__ == "__main__":
    rebuild_fe()
