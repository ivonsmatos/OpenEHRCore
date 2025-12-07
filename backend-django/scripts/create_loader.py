import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def create_loader():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Writing HeartbeatLoader.tsx...")
    
    # Check if 'src/components/ui' exists, create if not
    client.exec_command("mkdir -p /opt/openehrcore/frontend-pwa/src/components/ui")
    
    content = """
import React from 'react';
import { Activity } from 'lucide-react';

export const HeartbeatLoader: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <div className="relative flex items-center justify-center">
        {/* Ping effect background */}
        <div className="absolute w-20 h-20 bg-rose-500 rounded-full opacity-20 animate-ping"></div>
        {/* Core icon */}
        <Activity className="w-16 h-16 text-rose-600 animate-pulse" strokeWidth={2.5} />
      </div>
      <p className="mt-6 text-gray-600 font-medium animate-pulse tracking-wide">
        Carregando Sistema...
      </p>
    </div>
  );
};
"""
    # Use python to write content safely
    remote_script = f"""
import os
path = '/opt/openehrcore/frontend-pwa/src/components/ui/HeartbeatLoader.tsx'
content = {repr(content)}
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Written HeartbeatLoader.tsx")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/write_loader.py")
    client.exec_command("python3 /tmp/write_loader.py")
    
    client.close()

if __name__ == "__main__":
    create_loader()
