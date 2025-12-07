import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def verify_external_js():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # URL provided by user via logs (truncated hash, but I can emulate request to localhost)
    # The file in logs is: index-B3bNjmsM.js (based on my previous find)
    # User sees: main.js?attr=... which might be the injector?
    # Wait, "main.js" is rarely the vite output name. Vite uses "index-HASH.js".
    # User log says: "main.js?attr=..." AND "index-B3bNjmsM.js:12".
    # The error comes from "index-B3bNjmsM.js" (xhr).
    
    # I already checked index-B3bNjmsM.js in Step 9356 and it was CLEAN.
    
    # So if index-B3bNjmsM.js is CLEAN on disk.
    # And user sees error originating from it.
    # Then user has OLD VERSION of index-B3bNjmsM.js cached.
    
    # But wait, hash changes if content changes.
    # If I rebuilt, the hash SHOULD change if content changed.
    # index-B3bNjmsM was the hash "before" or "after"?
    # In Step 9344 (Before fix), I checked index-B3bNjmsM.js and it was FOUND.
    # In Step 9356 (After fix), I checked built image content... 
    # Wait, did I check the filename in Step 9356?
    # No, I used "grep -r", I didn't list filename.
    
    print("Listing assets to see if hash changed...")
    _, stdout, _ = client.exec_command("docker exec openehr_frontend ls -l /usr/share/nginx/html/assets")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    verify_external_js()
