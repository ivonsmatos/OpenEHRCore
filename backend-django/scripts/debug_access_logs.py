import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_access_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Nginx Access/Error Logs ---")
    # Nginx in docker usually directs access.log to stdout/stderr
    _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 50")
    print(stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("\n--- Recursive File List with Permissions ---")
    _, stdout, stderr = client.exec_command("docker exec openehr_frontend ls -lR /usr/share/nginx/html")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    debug_access_logs()
