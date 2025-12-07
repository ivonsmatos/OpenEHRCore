import os

def find_null_bytes(directory):
    for root, dirs, files in os.walk(directory):
        if 'venv' in dirs:
            dirs.remove('venv') # Ignorar venv
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        if b'\0' in f.read():
                            print(f"FOUND NULL BYTES: {path}")
                except Exception as e:
                    print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    print("Searching for null bytes in .py files...")
    find_null_bytes('.')
    print("Done.")
