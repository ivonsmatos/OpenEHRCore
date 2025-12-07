import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("Connected.")
        
        print("\n--- Postgres Logs ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_postgres --tail 50")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("\n--- HAPI FHIR Logs ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_hapi_fhir --tail 50")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("\n--- Django Logs ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_django --tail 50")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

        print("\n--- Frontend (Nginx) Logs ---")
        _, stdout, stderr = client.exec_command("docker logs openehr_frontend --tail 50")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("\n--- Docker PS ---")
        _, stdout, _ = client.exec_command("docker ps -a")
        print(stdout.read().decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug()
