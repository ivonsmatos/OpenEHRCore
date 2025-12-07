import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_network():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Docker Networks ---")
    _, stdout, _ = client.exec_command("docker network ls")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_network()
