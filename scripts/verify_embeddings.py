#!/usr/bin/env python3
"""
Verify vector embeddings are being generated correctly.
Run after deploying the eventing function and triggering documents.
"""

import os
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from dotenv import load_dotenv

load_dotenv()

COUCHBASE_CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING")
COUCHBASE_USER = os.getenv("COUCHBASE_USERNAME")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD")

def verify_embeddings():
    print("=" * 60)
    print("VECTOR EMBEDDING VERIFICATION")
    print("=" * 60)
    
    # Connect
    auth = PasswordAuthenticator(COUCHBASE_USER, COUCHBASE_PASSWORD)
    cluster = Cluster(COUCHBASE_CONNECTION_STRING, ClusterOptions(auth))
    
    # Count documents with/without vectors
    count_query = """
        SELECT 
            COUNT(*) FILTER (WHERE vector IS NOT MISSING) AS with_vector,
            COUNT(*) FILTER (WHERE vector IS MISSING AND type = "processed_patient_record") AS without_vector
        FROM pharma_knowledge._default.processed_documents
    """
    result = cluster.query(count_query)
    counts = list(result)[0]
    
    print(f"\nDocuments WITH vector:    {counts['with_vector']}")
    print(f"Documents WITHOUT vector: {counts['without_vector']}")
    
    if counts['with_vector'] == 0:
        print("\n[FAIL] No embeddings generated yet!")
        print("\nTrigger embeddings with this query in Capella Query Workbench:")
        print("-" * 60)
        print("""UPDATE pharma_knowledge._default.processed_documents
SET _trigger = NOW_MILLIS()
WHERE type = "processed_patient_record" AND vector IS MISSING
LIMIT 10;""")
        print("-" * 60)
        return False
    
    # Get sample document with vector
    sample_query = """
        SELECT META().id, medical_summary, ARRAY_LENGTH(vector) AS vector_dims
        FROM pharma_knowledge._default.processed_documents
        WHERE vector IS NOT MISSING
        LIMIT 3
    """
    result = cluster.query(sample_query)
    samples = list(result)
    
    print("\n" + "=" * 60)
    print("SAMPLE DOCUMENTS WITH EMBEDDINGS")
    print("=" * 60)
    
    for doc in samples:
        print(f"\nID: {doc['id']}")
        print(f"Vector Dimensions: {doc['vector_dims']}")
        print(f"Medical Summary: {doc.get('medical_summary', 'N/A')[:100]}...")
    
    # Validate dimensions (OpenAI text-embedding-3-small = 1536)
    if samples and samples[0]['vector_dims'] == 1536:
        print("\n[PASS] Vector dimensions correct (1536 for OpenAI text-embedding-3-small)")
    elif samples and samples[0]['vector_dims'] == 768:
        print("\n[INFO] Vector dimensions = 768 (HuggingFace BGE model)")
    elif samples:
        print(f"\n[WARN] Unexpected vector dimensions: {samples[0]['vector_dims']}")
    
    # Show first few vector values
    vector_query = """
        SELECT vector[0:5] AS first_5_values
        FROM pharma_knowledge._default.processed_documents
        WHERE vector IS NOT MISSING
        LIMIT 1
    """
    result = cluster.query(vector_query)
    vector_sample = list(result)
    if vector_sample:
        print(f"\nFirst 5 embedding values: {vector_sample[0]['first_5_values']}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    return counts['with_vector'] > 0

if __name__ == "__main__":
    verify_embeddings()
