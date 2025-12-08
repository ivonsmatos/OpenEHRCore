import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def upload_force():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    
    local_views = "c:\\Users\\ivonm\\OneDrive\\Documents\\GitHub\\OpenEHRCore\\backend-django\\fhir_api\\views_consent.py"
    remote_views = "/opt/openehrcore/backend-django/fhir_api/views_consent.py"
    
    local_urls = "c:\\Users\\ivonm\\OneDrive\\Documents\\GitHub\\OpenEHRCore\\backend-django\\fhir_api\\urls.py"
    remote_urls = "/opt/openehrcore/backend-django/fhir_api/urls.py"
    
    print(f"Uploading {local_views} to {remote_views}")
    sftp.put(local_views, remote_views)
    
    print(f"Uploading {local_urls} to {remote_urls}")
    sftp.put(local_urls, remote_urls)
    
    sftp.close()
    t.close()

if __name__ == "__main__":
    upload_force()
