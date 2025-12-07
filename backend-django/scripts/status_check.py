import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_status():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        print("\n--- Docker PS (Status) ---")
        _, stdout, _ = client.exec_command("docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'")
        print(stdout.read().decode())
        
        print("\n--- Frontend Logs (Tail 20) ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 20")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

        print("\n--- Django Logs (Tail 20) ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_django --tail 20")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_status()
