"""
Test Couchbase connection with your credentials
This will help diagnose authentication issues
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions

# Get credentials
endpoint = os.getenv("COUCHBASE_CONNECTION_STRING")
username = os.getenv("COUCHBASE_USERNAME")
password = os.getenv("COUCHBASE_PASSWORD")

print("="*70)
print("Couchbase Connection Test")
print("="*70)
print(f"Endpoint: {endpoint}")
print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
print()

if not all([endpoint, username, password]):
    print("ERROR: Missing credentials in .env file")
    sys.exit(1)

try:
    print("Attempting to connect...")
    auth = PasswordAuthenticator(username, password)
    options = ClusterOptions(auth)
    options.apply_profile("wan_development")
    
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=10))
    
    print("✓ Connection successful!")
    print()
    
    # Try to list buckets (requires admin permissions)
    try:
        bucket_manager = cluster.buckets()
        buckets = bucket_manager.get_all_buckets()
        print(f"✓ Found {len(buckets)} existing buckets:")
        for bucket in buckets.values():
            print(f"  - {bucket.name}")
    except Exception as e:
        print(f"⚠ Could not list buckets (may need admin permissions): {e}")
        print()
        print("This is OK if your user has bucket-level permissions only.")
    
    print()
    print("Connection test passed! You can proceed with setup.")
    
except Exception as e:
    print(f"✗ Connection failed!")
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("1. Check your username and password in .env file")
    print("2. Verify the cluster endpoint is correct")
    print("3. Check if your IP address is allowed in Capella")
    print("   (Go to Settings > Allowed IP Addresses)")
    print("4. Check if the cluster is active (not hibernated)")
    print("5. Verify user has 'Cluster Admin' or 'Bucket Admin' role")
    sys.exit(1)
