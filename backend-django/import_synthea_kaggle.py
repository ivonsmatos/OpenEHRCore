import kagglehub
import os
import glob
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FHIR_URL = "http://localhost:8080/fhir"
DATASET_NAME = "krsna540/synthea-dataset-jsons-ehr"

def download_dataset():
    """Download dataset using kagglehub"""
    logger.info(f"Downloading dataset: {DATASET_NAME}")
    try:
        path = kagglehub.dataset_download(DATASET_NAME)
        logger.info(f"Dataset downloaded to: {path}")
        return path
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        return None

def import_file(file_path):
    """Import a single FHIR JSON file to the server"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        resource_type = data.get('resourceType')
        if not resource_type:
            logger.warning(f"Skipping {file_path}: No resourceType found")
            return False

        # If it's a Bundle, we usually POST to the base URL
        if resource_type == 'Bundle':
            url = FHIR_URL
        else:
            url = f"{FHIR_URL}/{resource_type}"

        headers = {'Content-Type': 'application/json'}
        
        # Check if we need authentication (assuming Bypass for now based on seed scripts)
        # If needed: headers['Authorization'] = 'Bearer dev-token-bypass'

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info(f"Successfully imported {file_path} (Type: {resource_type})")
            return True
        else:
            logger.error(f"Failed to import {file_path}. Status: {response.status_code} Response: {response.text[:200]}")
            return False

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    path = download_dataset()
    if not path:
        return

    # Find all JSON files recursively
    json_files = glob.glob(os.path.join(path, "**", "*.json"), recursive=True)
    logger.info(f"Found {len(json_files)} JSON files")

    if not json_files:
        logger.warning("No JSON files found in the dataset path.")
        return

    success_count = 0
    failure_count = 0

    for file_path in json_files:
        # Skip package.json or other non-resource files if they exist (heuristic)
        if "package.json" in file_path:
            continue
            
        if import_file(file_path):
            success_count += 1
        else:
            failure_count += 1

    logger.info("Import completed.")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failure_count}")

if __name__ == "__main__":
    main()
