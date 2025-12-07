import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def update_urls():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    remote_script = """
import re
path = '/opt/openehrcore/backend-django/fhir_api/urls.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already exists
if 'list_patients' in content:
    print("Already exists")
    exit(0)

# Pattern: urlpatterns = [
# We insert after that.
new_line = "    path('patients/list/', views.list_patients, name='list_patients'),\\n"
content = content.replace("urlpatterns = [", "urlpatterns = [\\n" + new_line)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated urls.py")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/update_urls.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/update_urls.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Restart django
    client.exec_command("docker restart openehr_django")
    
    client.close()

if __name__ == "__main__":
    update_urls()
