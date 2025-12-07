import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_ssh():
    print(f"Connecting to {HOST}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS, timeout=20)
        print("SSH Connected OK")
        _, stdout, _ = client.exec_command("uptime")
        print("Uptime:", stdout.read().decode().strip())
        client.close()
    except Exception as e:
        print(f"SSH Failed: {e}")

if __name__ == "__main__":
    check_ssh()
