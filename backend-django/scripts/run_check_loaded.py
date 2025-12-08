import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # 1. Check if file exists inside container
    cmd_ls = "docker exec openehr_django ls /app/check_loaded.py"
    stdin, stdout, stderr = client.exec_command(cmd_ls)
    print("File check:", stdout.read().decode().strip() or stderr.read().decode().strip())
    
    # 2. Run it if exists
    cmd_run = "docker exec openehr_django python3 /app/check_loaded.py"
    stdin, stdout, stderr = client.exec_command(cmd_run)
    print("Output:")
    print(stdout.read().decode())
    print("Error:")
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    run_check()
