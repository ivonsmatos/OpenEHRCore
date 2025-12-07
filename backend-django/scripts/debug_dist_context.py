import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def debug_dist_ctx():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    _, stdout, _ = client.exec_command("docker exec openehr_frontend find /usr/share/nginx/html/assets -name 'index-*.js'")
    js_file = stdout.read().decode().strip()
    
    if js_file:
        print(f"Grepping {js_file}...")
        # grep -o prints only matched part, but we want context.
        # minified file is one line. grep will print HUGE line.
        # use grep -o with some regex to capturing surrounding chars?
        # grep -o '.\{0,100\}localhost:8000.\{0,100\}' 
        # Escape for shell: .\{0,100\} -> .\\{0,100\\}
        
        cmd = f"docker exec openehr_frontend grep -o '.\{{0,100\}}localhost:8000.\{{0,100\}}' {js_file}"
        _, stdout, stderr = client.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
    client.close()

if __name__ == "__main__":
    debug_dist_ctx()
