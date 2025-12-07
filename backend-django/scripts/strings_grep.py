import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def strings_grep():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Finding JS...")
    _, stdout, _ = client.exec_command("docker exec openehr_frontend find /usr/share/nginx/html/assets -name 'index-*.js'")
    js_file = stdout.read().decode().strip()
    
    if js_file:
        print(f"Strings on {js_file}...")
        cmd = f"docker exec openehr_frontend sh -c 'strings {js_file} | grep localhost:8000'"
        _, stdout, stderr = client.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    strings_grep()
