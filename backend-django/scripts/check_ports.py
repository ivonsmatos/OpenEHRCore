import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_ports():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Port 80 Check ---")
    _, stdout, _ = client.exec_command("netstat -tulpn | grep :80")
    print(stdout.read().decode())
    
    print("\n--- Docker PS ---")
    _, stdout, _ = client.exec_command("docker ps --format '{{.ID}} {{.Image}} {{.Ports}} {{.Names}}'")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_ports()
