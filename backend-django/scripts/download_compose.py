import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def download_compose():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    
    remote_path = "/opt/openehrcore/docker/docker-compose.yml"
    local_path = "c:\\Users\\ivonm\\OneDrive\\Documents\\GitHub\\OpenEHRCore\\backend-django\\docker-compose-remote.yml"
    
    sftp.get(remote_path, local_path)
    
    sftp.close()
    t.close()

if __name__ == "__main__":
    download_compose()
