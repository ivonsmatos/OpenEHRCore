import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_frontend_build():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Frontend Build Debug ---")
    cmd = "docker build --no-cache /opt/openehrcore/frontend-pwa"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    print("Exit Code:", stdout.channel.recv_exit_status())
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_frontend_build()
