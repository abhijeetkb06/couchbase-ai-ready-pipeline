"""
Trigger Embedding Generation for Existing Processed Documents

This script "touches" processed documents to trigger the vector_embedding_pipeline
eventing function. It updates documents in batches with a small delay to avoid
overwhelming the HuggingFace API rate limits.

Usage:
    python scripts/trigger_embeddings.py

Options:
    --batch-size    Number of documents per batch (default: 50)
    --delay         Seconds to wait between batches (default: 2)
    --limit         Maximum documents to process (default: all)
"""

import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Couchbase imports
try:
    from couchbase.cluster import Cluster
    from couchbase.auth import PasswordAuthenticator
    from couchbase.options import ClusterOptions, QueryOptions
    from couchbase.exceptions import CouchbaseException
    COUCHBASE_AVAILABLE = True
except ImportError:
    print("WARNING: Couchbase SDK not installed")
    COUCHBASE_AVAILABLE = False

# Configuration
COUCHBASE_CONFIG = {
    "connection_string": os.getenv("COUCHBASE_CONNECTION_STRING"),
    "username": os.getenv("COUCHBASE_USERNAME"),
    "password": os.getenv("COUCHBASE_PASSWORD"),
    "bucket": os.getenv("COUCHBASE_BUCKET", "pharma_knowledge")
}


def connect_to_couchbase():
    """Connect to Couchbase cluster"""
    if not COUCHBASE_AVAILABLE:
        return None, None
    
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
        print(f"Connected to bucket: {COUCHBASE_CONFIG['bucket']}")
        
        return cluster, bucket
        
    except CouchbaseException as e:
        print(f"Failed to connect to Couchbase: {e}")
        return None, None


def count_documents_needing_embeddings(cluster):
    """Count how many documents need embeddings"""
    query = """
        SELECT COUNT(*) as count
        FROM `pharma_knowledge`._default.processed_documents
        WHERE type = "processed_patient_record"
          AND embedding IS MISSING
    """
    result = cluster.query(query)
    for row in result:
        return row['count']
    return 0


def count_documents_with_embeddings(cluster):
    """Count how many documents already have embeddings"""
    query = """
        SELECT COUNT(*) as count
        FROM `pharma_knowledge`._default.processed_documents
        WHERE embedding IS NOT MISSING
    """
    result = cluster.query(query)
    for row in result:
        return row['count']
    return 0


def get_document_ids_without_embeddings(cluster, limit):
    """Get document IDs that need embeddings"""
    query = f"""
        SELECT META().id as doc_id
        FROM `pharma_knowledge`._default.processed_documents
        WHERE type = "processed_patient_record"
          AND embedding IS MISSING
        LIMIT {limit}
    """
    result = cluster.query(query)
    return [row['doc_id'] for row in result]


def trigger_embedding_batch(collection, doc_ids):
    """Trigger embedding generation by updating documents"""
    triggered = 0
    errors = 0
    
    for doc_id in doc_ids:
        try:
            # Get the document
            result = collection.get(doc_id)
            doc = result.content_as[dict]
            
            # Touch the document to trigger eventing
            doc['embedding_triggered_at'] = datetime.utcnow().isoformat()
            
            # Write it back (this triggers OnUpdate in eventing)
            collection.upsert(doc_id, doc)
            triggered += 1
            
        except Exception as e:
            print(f"  Error triggering {doc_id}: {e}")
            errors += 1
    
    return triggered, errors


def main():
    parser = argparse.ArgumentParser(description='Trigger embedding generation for processed documents')
    parser.add_argument('--batch-size', type=int, default=50, help='Documents per batch (default: 50)')
    parser.add_argument('--delay', type=float, default=2.0, help='Seconds between batches (default: 2)')
    parser.add_argument('--limit', type=int, default=0, help='Max documents to process (default: all)')
    args = parser.parse_args()
    
    print("="*70)
    print("Trigger Embedding Generation")
    print("="*70)
    
    if not COUCHBASE_AVAILABLE:
        print("\nCouchbase SDK not installed")
        print("Run: pip install couchbase")
        return
    
    # Connect
    cluster, bucket = connect_to_couchbase()
    if bucket is None:
        print("\nCould not connect to Couchbase")
        return
    
    collection = bucket.scope("_default").collection("processed_documents")
    
    # Get counts
    need_embeddings = count_documents_needing_embeddings(cluster)
    have_embeddings = count_documents_with_embeddings(cluster)
    
    print(f"\nCurrent status:")
    print(f"  Documents WITH embeddings: {have_embeddings}")
    print(f"  Documents needing embeddings: {need_embeddings}")
    
    if need_embeddings == 0:
        print("\nAll documents already have embeddings!")
        return
    
    # Determine how many to process
    to_process = args.limit if args.limit > 0 else need_embeddings
    to_process = min(to_process, need_embeddings)
    
    print(f"\nWill trigger {to_process} documents")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Delay between batches: {args.delay}s")
    
    estimated_time = (to_process / args.batch_size) * (args.delay + 1)  # rough estimate
    print(f"  Estimated time: {estimated_time/60:.1f} minutes")
    
    input("\nPress Enter to start (Ctrl+C to cancel)...")
    
    # Process in batches
    total_triggered = 0
    total_errors = 0
    start_time = datetime.now()
    
    while total_triggered < to_process:
        # Get next batch of document IDs
        remaining = to_process - total_triggered
        batch_limit = min(args.batch_size, remaining)
        
        doc_ids = get_document_ids_without_embeddings(cluster, batch_limit)
        
        if not doc_ids:
            print("\nNo more documents to process")
            break
        
        # Trigger this batch
        triggered, errors = trigger_embedding_batch(collection, doc_ids)
        total_triggered += triggered
        total_errors += errors
        
        progress = (total_triggered / to_process) * 100
        print(f"  Progress: {total_triggered}/{to_process} ({progress:.1f}%) - Batch: {triggered} triggered, {errors} errors")
        
        # Delay before next batch (to respect API rate limits)
        if total_triggered < to_process:
            time.sleep(args.delay)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("Embedding Trigger Complete")
    print("="*70)
    print(f"  Total triggered: {total_triggered}")
    print(f"  Total errors: {total_errors}")
    print(f"  Time taken: {duration:.1f} seconds")
    print("\nNote: Embeddings are generated asynchronously by the eventing function.")
    print("Check document embedding_status field for completion status.")
    print("\nTo verify progress, run this query:")
    print("""
    SELECT 
        embedding_status, 
        COUNT(*) as count
    FROM `pharma_knowledge`._default.processed_documents
    WHERE type = "processed_patient_record"
    GROUP BY embedding_status;
    """)


if __name__ == "__main__":
    main()
