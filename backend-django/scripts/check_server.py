
import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def run_command(ssh, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out:
        print(f"[OUT]\n{out}")
    if err:
        print(f"[ERR]\n{err}")
    
    return exit_status, out

def check_server():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("Connected successfully.\n")
        
        print("--- OS Info ---")
        run_command(client, "cat /etc/os-release")
        
        print("\n--- Resources ---")
        run_command(client, "free -h")
        run_command(client, "df -h /")
        run_command(client, "nproc")
        
        print("\n--- Docker Check ---")
        code, _ = run_command(client, "docker --version")
        if code != 0:
            print("Docker NOT installed.")
        
        print("\n--- Docker Compose Check ---")
        code, _ = run_command(client, "docker-compose --version")
        if code != 0:
             # Try docker compose plugin
             run_command(client, "docker compose version")

        print("\n--- Ports Check ---")
        run_command(client, "netstat -tulpn | grep LISTEN")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_server()
