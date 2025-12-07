import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def refactor_loader():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("Refactoring HeartbeatLoader.tsx...")
    
    content = """
import React from 'react';
import { Activity } from 'lucide-react';

interface HeartbeatLoaderProps {
  fullScreen?: boolean;
  label?: string;
}

export const HeartbeatLoader: React.FC<HeartbeatLoaderProps> = ({ fullScreen = true, label }) => {
  const containerClass = fullScreen
    ? "flex flex-col items-center justify-center h-screen bg-gray-50 fixed inset-0 z-50"
    : "flex flex-col items-center justify-center h-full min-h-[200px] w-full p-4";

  const text = label || (fullScreen ? "Carregando Sistema..." : "Carregando...");

  return (
    <div className={containerClass}>
      <div className="relative flex items-center justify-center">
        {/* Ping effect background */}
        <div className="absolute w-16 h-16 bg-rose-500 rounded-full opacity-20 animate-ping"></div>
        {/* Core icon */}
        <Activity className="w-12 h-12 text-rose-600 animate-pulse" strokeWidth={2.5} />
      </div>
      <p className="mt-4 text-gray-600 font-medium animate-pulse tracking-wide text-sm">
        {text}
      </p>
    </div>
  );
};
"""
    remote_script = f"""
path = '/opt/openehrcore/frontend-pwa/src/components/ui/HeartbeatLoader.tsx'
content = {repr(content)}
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated HeartbeatLoader.tsx")
"""
    client.exec_command("echo \"" + remote_script.replace('"', '\\"') + "\" > /tmp/upd_ldr.py")
    client.exec_command("python3 /tmp/upd_ldr.py")
    
    client.close()

if __name__ == "__main__":
    refactor_loader()
