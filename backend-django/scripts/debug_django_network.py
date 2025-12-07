import paramiko
import sys
import json

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_django_network():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Finding Django container...")
    _, stdout, _ = client.exec_command("docker ps -q -f name=django")
    cid = stdout.read().decode().strip()
    
    if not cid:
        print("Django container NOT FOUND!")
        client.close()
        return

    print(f"Inspecting Django {cid}...")
    _, stdout, _ = client.exec_command(f"docker inspect {cid}")
    data = stdout.read().decode()
    
    try:
        inspect = json.loads(data)[0]
        networks = inspect['NetworkSettings']['Networks']
        for net_name, net_conf in networks.items():
            print(f"Network: {net_name}")
            print(f"Aliases: {net_conf.get('Aliases')}")
    except Exception as e:
        print(f"Error parsing json: {e}")
        print(data[:500]) # print bit of raw data
    
    client.close()

if __name__ == "__main__":
    debug_django_network()
