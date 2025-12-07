import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_load():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=10)
    
    print("Uptime/Load:")
    _, stdout, _ = client.exec_command("uptime")
    print(stdout.read().decode())
    
    print("Docker Stats:")
    _, stdout, _ = client.exec_command("docker stats --no-stream --format '{{.Name}}: {{.CPUPerc}} / {{.MemPerc}}'")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_load()
