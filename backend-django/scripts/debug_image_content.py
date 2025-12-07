import paramiko
import sys
import time

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_image_content():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("\n--- Image Content Check ---")
    cmd = "docker run --rm frontend_debug ls -laR /usr/share/nginx/html"
    _, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    print("STDOUT:", out)
    if err: console.log("STDERR:", err) # oops, print
    
    client.close()

if __name__ == "__main__":
    debug_image_content()
