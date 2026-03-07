"""
Download Healthcare Dataset from Kaggle (10,000 patient records)

Dataset: Healthcare Dataset by Prasad
Link: https://www.kaggle.com/datasets/prasad22/healthcare-dataset

This dataset contains 10,000 patient records with:
- Patient names (to be redacted)
- Medical record numbers (to be redacted)
- Dates of admission
- Medical conditions (to be extracted as metadata)
- Doctors, hospitals, medications
- Billing information

Perfect for demonstrating PII redaction and metadata enrichment at scale!

Prerequisites:
1. Install Kaggle CLI: pip install kaggle
2. Add KAGGLE_API_TOKEN to .env file
"""

import os
import sys
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATASET_NAME = "prasad22/healthcare-dataset"


def check_kaggle_setup():
    """Check if Kaggle CLI is installed and configured"""
    print("Checking Kaggle CLI setup...")
    
    # Check if kaggle is installed
    try:
        result = subprocess.run(["kaggle", "--version"], capture_output=True, text=True)
        print(f"✓ Kaggle CLI installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print(" Kaggle CLI not found")
        print("\nPlease install it:")
        print("  pip install kaggle")
        sys.exit(1)
    
    # Check if KAGGLE_API_TOKEN is set
    kaggle_token = os.getenv("KAGGLE_API_TOKEN")
    if not kaggle_token:
        print(" KAGGLE_API_TOKEN not found in .env file")
        print("\nPlease add it to your .env file:")
        print("1. Go to https://www.kaggle.com/settings/account")
        print("2. Scroll to 'API' section")
        print("3. Click 'Create New API Token'")
        print("4. Copy the token and add to .env:")
        print("   KAGGLE_API_TOKEN=your_token_here")
        sys.exit(1)
    
    print(f"✓ Kaggle API token found in .env")
    
    # Set the environment variable for kaggle CLI
    os.environ["KAGGLE_API_TOKEN"] = kaggle_token


def download_dataset():
    """Download the healthcare dataset from Kaggle"""
    print(f"\nDownloading dataset: {DATASET_NAME}")
    print(f"Destination: {DATA_DIR}")
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download dataset
    try:
        subprocess.run([
            "kaggle", "datasets", "download",
            "-d", DATASET_NAME,
            "-p", str(DATA_DIR),
            "--unzip"
        ], check=True)
        
        print("✓ Dataset downloaded successfully!")
        
        # List downloaded files
        print("\nDownloaded files:")
        for file in DATA_DIR.glob("*.csv"):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({size_mb:.2f} MB)")
        
    except subprocess.CalledProcessError as e:
        print(f" Error downloading dataset: {e}")
        sys.exit(1)


def main():
    print("="*70)
    print("Download Healthcare Dataset from Kaggle")
    print("="*70)
    
    # Check setup
    check_kaggle_setup()
    
    # Download dataset
    download_dataset()
    
    print("\n" + "="*70)
    print("✓ Download complete!")
    print("="*70)
    print("\nNext step:")
    print("  python scripts/load_healthcare_data.py")
    print("\nThis will load 10,000 patient records into Couchbase")


if __name__ == "__main__":
    main()
