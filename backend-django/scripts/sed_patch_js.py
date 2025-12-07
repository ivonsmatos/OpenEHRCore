import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def patch_js():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Patching JS files directly in container...")
    # Using python code inside to avoid sed dialect issues
    
    # Actually sed is fine if simple.
    # localhost:8000 -> 45.151.122.234 (Len 14 -> 14)
    
    cmd = "docker exec openehr_frontend sed -i 's/localhost:8000/45.151.122.234/g' /usr/share/nginx/html/assets/index-*.js"
    # Wildcard expansion inside sh -c check?
    # docker exec direct wildcard might fail if local shell expands.
    # Wrap in sh -c
    
    full_cmd = "docker exec openehr_frontend sh -c \"sed -i 's/localhost:8000/45.151.122.234/g' /usr/share/nginx/html/assets/*.js\""
    
    _, stdout, stderr = client.exec_command(full_cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if err:
        print("STDERR:", err)
    else:
        print("Patch command executed.")
        
    print("Verifying patch...")
    cmd_ver = "docker exec openehr_frontend sh -c \"grep '45.151.122.234' /usr/share/nginx/html/assets/*.js\""
    _, stdout, _ = client.exec_command(cmd_ver)
    if "45.151.122.234" in stdout.read().decode():
        print("SUCCESS: IP found in JS.")
    else:
        print("WARNING: IP NOT found (Maybe text wasn't localhost:8000?)")
        
    client.close()

if __name__ == "__main__":
    patch_js()
