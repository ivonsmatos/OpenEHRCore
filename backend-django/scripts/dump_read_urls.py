import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def dump_read():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Dumping...")
    client.exec_command("cat /opt/openehrcore/backend-django/fhir_api/urls.py > /tmp/urls_dump.txt")
    time.sleep(1)
    
    # Read chunks
    for i in range(0, 5): # Read 100 lines total (5 chunks of 20)
        start = i * 20 + 1
        end = (i + 1) * 20
        cmd = f"sed -n '{start},{end}p' /tmp/urls_dump.txt"
        _, stdout, _ = client.exec_command(cmd)
        out = stdout.read().decode()
        if out:
            print(f"--- Lines {start}-{end} ---")
            print(out)
        else:
            break
            
    client.close()

if __name__ == "__main__":
    dump_read()
