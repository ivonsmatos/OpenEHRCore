import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_envs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Checking for .env files...")
    _, stdout, stderr = client.exec_command("ls -la /opt/openehrcore/frontend-pwa/.env*")
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if out:
        print("Found env files:")
        print(out)
        # Read them
        for line in out.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 9:
                fname = parts[-1] # filename is last
                if fname.startswith('/'): # absolute path from ls
                     print(f"--- Content of {fname} ---")
                     _, cat_out, _ = client.exec_command(f"cat {fname}")
                     print(cat_out.read().decode())
    else:
        print("No .env files found (ls output empty). error:", err)

    client.close()

if __name__ == "__main__":
    check_envs()
