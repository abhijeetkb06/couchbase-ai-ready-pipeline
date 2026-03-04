"""
Load Healthcare Dataset into Couchbase (10,000 patient records)

Loads data into raw_documents collection with status "pending"
Eventing function will automatically process them into processed_documents

OPTIMIZED VERSION: Uses parallel processing with ThreadPoolExecutor for 10x faster loads

Expected CSV columns:
- Name (PII - will be redacted)
- Age
- Gender
- Blood Type
- Medical Condition
- Date of Admission
- Doctor
- Hospital
- Insurance Provider
- Billing Amount
- Room Number
- Admission Type
- Discharge Date
- Medication
- Test Results
"""

import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load environment variables
load_dotenv()

# Couchbase imports
try:
    from couchbase.cluster import Cluster
    from couchbase.auth import PasswordAuthenticator
    from couchbase.options import ClusterOptions
    from couchbase.exceptions import CouchbaseException
    COUCHBASE_AVAILABLE = True
except ImportError:
    print("WARNING: Couchbase SDK not installed")
    COUCHBASE_AVAILABLE = False

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
CSV_FILE = DATA_DIR / "healthcare_dataset.csv"

COUCHBASE_CONFIG = {
    "connection_string": os.getenv("COUCHBASE_CONNECTION_STRING"),
    "username": os.getenv("COUCHBASE_USERNAME"),
    "password": os.getenv("COUCHBASE_PASSWORD"),
    "bucket": os.getenv("COUCHBASE_BUCKET", "pharma_knowledge")
}

# Performance tuning
NUM_THREADS = 10  # Parallel processing threads
BATCH_SIZE = 100   # Progress reporting interval

# Thread-safe counters
loaded_count = 0
error_count = 0
counter_lock = Lock()


def connect_to_couchbase():
    """Connect to Couchbase cluster"""
    if not COUCHBASE_AVAILABLE:
        return None
    
    try:
        print(f"Connecting to Couchbase: {COUCHBASE_CONFIG['connection_string']}")
        
        auth = PasswordAuthenticator(
            COUCHBASE_CONFIG["username"],
            COUCHBASE_CONFIG["password"]
        )
        options = ClusterOptions(auth)
        options.apply_profile("wan_development")
        
        cluster = Cluster(COUCHBASE_CONFIG["connection_string"], options)
        cluster.wait_until_ready(timedelta(seconds=10))
        
        bucket = cluster.bucket(COUCHBASE_CONFIG["bucket"])
        print(f"✓ Connected to bucket: {COUCHBASE_CONFIG['bucket']}")
        
        return cluster, bucket
        
    except CouchbaseException as e:
        print(f"Failed to connect to Couchbase: {e}")
        return None, None


def load_healthcare_data(bucket):
    """Load healthcare dataset from CSV into raw_documents collection with parallel processing"""
    global loaded_count, error_count
    
    if not CSV_FILE.exists():
        print(f"❌ CSV file not found: {CSV_FILE}")
        print("\nPlease run first:")
        print("  python scripts/download_kaggle_data.py")
        return 0
    
    print(f"\nLoading data from: {CSV_FILE}")
    print(f"Using {NUM_THREADS} parallel threads for maximum speed...")
    
    collection = bucket.scope("_default").collection("raw_documents")
    
    # Read all rows first
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    total_rows = len(rows)
    print(f"Total records to load: {total_rows}")
    
    # Reset counters
    loaded_count = 0
    error_count = 0
    
    def load_single_record(index_and_row):
        """Load a single record (thread worker function)"""
        global loaded_count, error_count
        
        index, row = index_and_row
        
        try:
            # Create document with PII included (will be redacted by eventing)
            doc_id = f"patient::{row['Name'].replace(' ', '_').lower()}::{index + 1}"
            
            document = {
                "_id": doc_id,
                "type": "patient_record",
                "processing_status": "pending",  # Trigger for eventing
                "created_at": datetime.utcnow().isoformat(),
                
                # Patient data (contains PII)
                "name": row['Name'],  # PII - will be redacted
                "age": int(row['Age']),
                "gender": row['Gender'],
                "blood_type": row['Blood Type'],
                
                # Medical data
                "medical_condition": row['Medical Condition'],
                "date_of_admission": row['Date of Admission'],
                "doctor": row['Doctor'],
                "hospital": row['Hospital'],
                "admission_type": row['Admission Type'],
                "discharge_date": row['Discharge Date'],
                "medication": row['Medication'],
                "test_results": row['Test Results'],
                
                # Billing data
                "insurance_provider": row['Insurance Provider'],
                "billing_amount": float(row['Billing Amount']),
                "room_number": int(row['Room Number'])
            }
            
            collection.upsert(doc_id, document)
            
            with counter_lock:
                loaded_count += 1
                if loaded_count % BATCH_SIZE == 0:
                    progress = (loaded_count / total_rows) * 100
                    print(f"  Progress: {loaded_count}/{total_rows} ({progress:.1f}%)")
            
            return True
            
        except Exception as e:
            with counter_lock:
                error_count += 1
            print(f"  Error loading record {index}: {e}")
            return False
    
    # Process records in parallel
    print("\nStarting parallel load...")
    start_time = datetime.now()
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Submit all tasks
        futures = [executor.submit(load_single_record, (i, row)) for i, row in enumerate(rows)]
        
        # Wait for completion
        for future in as_completed(futures):
            future.result()  # This will raise any exceptions
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✓ Loaded {loaded_count} patient records into raw_documents")
    print(f"✗ Failed: {error_count} records")
    print(f"⚡ Time taken: {duration:.2f} seconds")
    
    return loaded_count


def main():
    """Main function"""
    print("="*70)
    print("Load Healthcare Dataset into Couchbase")
    print("="*70)
    
    if not COUCHBASE_AVAILABLE:
        print("\n❌ Couchbase SDK not installed")
        print("Run: pip install couchbase")
        return
    
    # Connect to Couchbase
    cluster, bucket = connect_to_couchbase()
    
    if bucket is None:
        print("\n❌ Could not connect to Couchbase")
        print("Check your .env file credentials")
        return
    
    # Load data
    total = load_healthcare_data(bucket)
    
    print("\n" + "="*70)
    print(f"✓ Data load complete! {total} records inserted")
    print("="*70)
    print("\n📊 What happens next:")
    print("  1. Documents land in 'raw_documents' with status='pending'")
    print("  2. Eventing function triggers automatically")
    print("  3. PII gets redacted (names → [NAME_REDACTED])")
    print("  4. Metadata gets enriched (medical conditions extracted)")
    print("  5. Clean documents appear in 'processed_documents'")
    print("\n🔍 To watch the pipeline:")
    print("  - Capella UI → Data Tools → Documents")
    print("  - View raw_documents (with PII)")
    print("  - View processed_documents (clean)")
    print("\n💡 Next step:")
    print("  Deploy the eventing function in Capella UI")
    print("  See: eventing/knowledge_pipeline.js")


if __name__ == "__main__":
    main()
