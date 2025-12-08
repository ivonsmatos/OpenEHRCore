import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def update_urls_consent():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    remote_script = """
import os

path = '/opt/openehrcore/backend-django/fhir_api/urls.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'views_consent' not in content:
    content = "from . import views_consent\\n" + content
    
    # Append to urlpatterns
    extra_urls = "\\nurlpatterns += [\\n    path('consents/', views_consent.create_consent, name='create_consent'),\\n    path('consents/list/', views_consent.list_consents, name='list_consents'),\\n]\\n"
    
    # Insert before router.urls if exists, or append
    if 'urlpatterns += router.urls' in content:
        content = content.replace('urlpatterns += router.urls', extra_urls + 'urlpatterns += router.urls')
    else:
        content += extra_urls

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated urls.py with consent routes")
else:
    print("Already updated")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/update_uc.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/update_uc.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Restart django to apply changes
    client.exec_command("docker restart openehr_django")
    
    client.close()

if __name__ == "__main__":
    update_urls_consent()
