
import os
import requests
from tqdm import tqdm

# Configuration
MODEL_REPO = "TheBloke/BioMistral-7B-GGUF"
MODEL_FILE = "biomistral-7b.Q4_K_M.gguf"
DOWNLOAD_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}"
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Check if file exists and has correct size
    if os.path.exists(filename):
        if os.path.getsize(filename) == total_size:
            print(f"✅ Model {os.path.basename(filename)} already exists and is complete.")
            return True
        else:
            print(f"⚠️ Model exists but size mismatch. Redownloading...")
    
    print(f"⬇️ Downloading {MODEL_FILE}...")
    print(f"   Source: {url}")
    print(f"   Destination: {filename}")
    print(f"   Size: {total_size / (1024*1024):.2f} MB")

    block_size = 1024 * 1024 # 1MB
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
    
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
            
    progress_bar.close()
    
    if total_size != 0 and os.path.getsize(filename) != total_size:
        print("❌ Download failed (Size mismatch).")
        return False
    
    print("✅ Download finished successfully!")
    return True

if __name__ == "__main__":
    # Ensure models directory exists
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Created models directory: {MODELS_DIR}")
    
    target_path = os.path.join(MODELS_DIR, MODEL_FILE)
    
    try:
        success = download_file(DOWNLOAD_URL, target_path)
        if success:
            print(f"\n🎉 Model ready at: {target_path}")
            print("You can now run the BioMistral integration.")
        else:
            exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Download cancelled by user.")
        # Optional: cleanup partial file
    except Exception as e:
        print(f"\n❌ Error: {e}")
