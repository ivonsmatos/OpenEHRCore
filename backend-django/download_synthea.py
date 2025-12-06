
import kagglehub
import os

print("Starting download...")
try:
    # Download latest version
    path = kagglehub.dataset_download("krsna540/synthea-dataset-jsons-ehr")
    print(f"SUCCESS: Dataset downloaded to: {path}")
    
    # List first few files to confirm
    files = os.listdir(path)
    print(f"Found {len(files)} files.")
    print("First 5 files:", files[:5])
    
except Exception as e:
    print(f"ERROR: Failed to download dataset. {e}")
