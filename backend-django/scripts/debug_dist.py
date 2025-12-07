import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_dist_content():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Finding main JS file in container...")
    # Find the main js asset
    _, stdout, _ = client.exec_command("docker exec openehr_frontend find /usr/share/nginx/html/assets -name 'index-*.js'")
    js_file = stdout.read().decode().strip()
    
    if not js_file:
        print("JS file not found!")
    else:
        print(f"Checking content of {js_file} for localhost:8000...")
        # Grep inside the MINIFIED file inside container
        _, stdout, stderr = client.exec_command(f"docker exec openehr_frontend grep 'localhost:8000' {js_file}")
        out = stdout.read().decode()
        if out:
            print("FOUND localhost:8000 in built asset! Build did not update code.")
        else:
            print("NOT FOUND in built asset. The server code is clean.")
            
    client.close()

if __name__ == "__main__":
    debug_dist_content()
