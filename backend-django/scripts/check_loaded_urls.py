import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def check_loaded():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    remote_script = """
import os
import django
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api import urls
print("URLs loaded in fhir_api.urls:")
for p in urls.urlpatterns:
    print(p)
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/check_loaded_urls.py")
    
    # We need to run this INSIDE the container
    cmd = "docker exec openehr_django python3 /tmp/check_loaded_urls.py"
    # Note: /tmp is mounted? No.
    # We need to put the script INSIDE the container or cat it into stdin.
    
    # Let's write to /opt/openehrcore/backend-django/check_loaded.py which is mounted at /app?
    # Yes, /opt/openehrcore/backend-django is mounted to /app usually.
    
    pass

def check_loaded_v2():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    
    script_content = """import os
import django
import sys
from django.conf import settings

# /app is likely in python path but let's be sure
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openehrcore.settings')
django.setup()

from fhir_api import urls
print("-- START URLS --")
for p in urls.urlpatterns:
    print(p)
print("-- END URLS --")
"""
    
    sftp.open("/opt/openehrcore/backend-django/check_loaded.py", "w").write(script_content)
    sftp.close()
    t.close()
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    stdin, stdout, stderr = client.exec_command("docker exec openehr_django python3 /app/check_loaded.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    client.close()

if __name__ == "__main__":
    check_loaded_v2()
