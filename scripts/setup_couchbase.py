"""
Simplified Couchbase Capella Setup Script for Knowledge Preparation Layer Demo

This script creates:
1. Bucket: pharma_knowledge (manual - must exist)
2. Collections: raw_documents, processed_documents
3. Indexes for querying

SIMPLE ARCHITECTURE:
- raw_documents: Incoming data with PII
- processed_documents: Clean, enriched, searchable data
"""

import os
import sys
import time
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
from couchbase.exceptions import (
    CollectionAlreadyExistsException,
    QueryIndexAlreadyExistsException
)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration - Loaded from .env file
COUCHBASE_CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING")
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD")
BUCKET_NAME = os.getenv("COUCHBASE_BUCKET", "pharma_knowledge")


def connect_to_cluster():
    """Connect to Couchbase Capella cluster"""
    print(f"Connecting to Couchbase at {COUCHBASE_CONNECTION_STRING}...")
    
    if not COUCHBASE_PASSWORD:
        print("ERROR: COUCHBASE_PASSWORD environment variable not set")
        print("Please check your .env file")
        sys.exit(1)
    
    # Connect to Capella using ClusterOptions (Python SDK 4.x)
    auth = PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD)
    options = ClusterOptions(auth)
    # Use wan_development profile for Capella to avoid latency issues
    options.apply_profile("wan_development")
    
    cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)
    
    # Wait for cluster to be ready
    cluster.wait_until_ready(timedelta(seconds=10))
    print("✓ Connected to Couchbase")
    return cluster


def create_collections(cluster):
    """Create the two main collections"""
    print(f"\nSetting up collections in bucket '{BUCKET_NAME}'...")
    bucket = cluster.bucket(BUCKET_NAME)
    collection_manager = bucket.collections()
    
    # Use default scope
    scope_name = "_default"
    
    collections = [
        "raw_documents",
        "processed_documents",
        "metadata"
    ]
    
    for collection_name in collections:
        try:
            from couchbase.management.collections import CollectionSpec
            
            # Try to create the collection
            collection_spec = CollectionSpec(collection_name, scope_name)
            collection_manager.create_collection(collection_spec)
            print(f"✓ Collection '{scope_name}.{collection_name}' created")
            time.sleep(1)
            
        except CollectionAlreadyExistsException:
            print(f"  → Collection '{scope_name}.{collection_name}' already exists")
        except Exception as e:
            print(f"  ⚠ Note: {e}")
            print(f"  → Collection '{collection_name}' will be created on first data insert")
    
    print("✓ Collections setup complete")


def create_indexes(cluster):
    """Create indexes for querying"""
    print(f"\nCreating indexes...")
    
    indexes = [
        # Primary indexes for both collections
        {
            "name": "idx_primary_raw",
            "query": f"CREATE PRIMARY INDEX idx_primary_raw ON `{BUCKET_NAME}`.`_default`.`raw_documents`"
        },
        {
            "name": "idx_primary_processed",
            "query": f"CREATE PRIMARY INDEX idx_primary_processed ON `{BUCKET_NAME}`.`_default`.`processed_documents`"
        },
        
        # Secondary index on processing_status for raw documents
        {
            "name": "idx_processing_status",
            "query": f"CREATE INDEX idx_processing_status ON `{BUCKET_NAME}`.`_default`.`raw_documents`(processing_status) WHERE processing_status IS NOT MISSING"
        },
        
        # Indexes on processed documents for demo queries
        {
            "name": "idx_medical_condition",
            "query": f"CREATE INDEX idx_medical_condition ON `{BUCKET_NAME}`.`_default`.`processed_documents`(medical_condition) WHERE medical_condition IS NOT MISSING"
        },
        {
            "name": "idx_doctor",
            "query": f"CREATE INDEX idx_doctor ON `{BUCKET_NAME}`.`_default`.`processed_documents`(doctor) WHERE doctor IS NOT MISSING"
        }
    ]
    
    for index in indexes:
        try:
            cluster.query(index["query"]).execute()
            print(f"✓ Index '{index['name']}' created")
        except QueryIndexAlreadyExistsException:
            print(f"  → Index '{index['name']}' already exists")
        except Exception as e:
            print(f"  ⚠ Warning: Could not create index '{index['name']}': {e}")


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*70)
    print("✓ Simplified Couchbase setup complete!")
    print("="*70)
    print("\n📁 Structure:")
    print(f"   Bucket: {BUCKET_NAME}")
    print(f"   └── _default (scope)")
    print(f"       ├── raw_documents (incoming data with PII)")
    print(f"       ├── processed_documents (clean, enriched data)")
    print(f"       └── metadata (eventing storage/checkpoints)")
    print("\n🔄 Data Flow:")
    print("   raw_documents → [Eventing] → processed_documents")
    print("\n📋 Next steps:")
    print("1. Download Kaggle healthcare dataset:")
    print("   python scripts/download_kaggle_data.py")
    print("\n2. Load data into Couchbase:")
    print("   python scripts/load_healthcare_data.py")
    print("\n3. Deploy eventing function in Capella UI:")
    print("   - Go to Data Tools > Eventing")
    print("   - Import: eventing/knowledge_pipeline.js")
    print("   - Configure bucket binding for processed_documents")
    print("   - Deploy and start")
    print("\n4. Watch 10,000 records transform in real-time!")
    print("="*70)


def main():
    """Main setup function"""
    print("="*70)
    print("Couchbase Knowledge Preparation Layer - Simplified Setup")
    print("="*70)
    
    try:
        # Connect to cluster
        cluster = connect_to_cluster()
        
        # Create collections
        create_collections(cluster)
        
        # Create indexes
        create_indexes(cluster)
        
        # Print next steps
        print_next_steps()
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
