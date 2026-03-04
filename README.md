# Couchbase AI-Ready Data Pipeline

A demonstration of the **Knowledge Preparation Layer** - the critical step BEFORE retrieval in any RAG (Retrieval-Augmented Generation) pipeline.

This project shows how Couchbase Capella's Eventing Service can automatically transform raw, messy, PII-laden data into clean, enriched, retrieval-ready documents at scale - in real-time, with zero ETL pipelines.

## What It Does

1. **PII Redaction** - Automatically redacts patient names and sensitive identifiers (HIPAA-compliant)
2. **Metadata Enrichment** - Classifies age groups, billing categories, and standardizes test results
3. **Data Structuring** - Organizes flat records into nested, queryable document structures
4. **Audit Trail** - Captures what was redacted, when, and compliance flags for governance

## Bucket Structure

The project uses a single Couchbase bucket `pharma_knowledge` organized into scopes and collections:

```
pharma_knowledge (bucket)
├── _default (scope)                    — Main application data
│   ├── raw_documents                   — Raw patient records land here (with PII)
│   ├── processed_documents             — Clean, enriched, retrieval-ready documents
│   ├── stats                           — Pipeline statistics and counters
│   └── _default                        — System default (unused)
│
├── storage (scope)                     — Eventing internal storage
│   └── metadata                        — Eventing checkpoints and state tracking
│
└── _system (scope)                     — Couchbase system scope (managed automatically)
```

### How data flows through the collections

1. **`raw_documents`** -- The `load_healthcare_data.py` script inserts patient records here with `processing_status: "pending"`. These records contain raw PII (patient names), unstructured metadata, and flat fields straight from the source CSV.

2. **`processed_documents`** -- The Eventing function `knowledge_pipeline` watches `raw_documents`. When it detects a document with `processing_status: "pending"`, it automatically:
   - Redacts PII (patient names become `[NAME_REDACTED]`)
   - Enriches metadata (age groups, billing categories, test result classifications)
   - Restructures the flat record into nested objects (patient, medical, billing, metrics)
   - Writes the clean document here with `is_pii_compliant: true` and `is_searchable: true`
   
   This collection is what downstream AI/search applications query -- every document is HIPAA-compliant and retrieval-ready.

3. **`stats`** -- Stores pipeline-level statistics (e.g., total documents processed, processing rates).

4. **`storage.metadata`** -- Used internally by the Couchbase Eventing Service to track function checkpoints, progress, and DCP stream state. You configure this when deploying the eventing function but never read/write to it from application code.

### Data flow diagram

```
  CSV Dataset
      │
      ▼
  load_healthcare_data.py
      │
      ▼
  raw_documents  ──── Eventing Function ────►  processed_documents
  (PII, flat)         [Redact → Enrich]         (Clean, structured)
                            │
                            ▼
                    storage.metadata
                    (checkpoints)
```

## Prerequisites

- Python 3.9+
- A [Couchbase Capella](https://cloud.couchbase.com/) cluster with a bucket named `pharma_knowledge`

## Security Notice

**DO NOT commit private keys, passwords, or API tokens to GitHub.**

This project uses a `.env` file for all credentials. The `.env` file is listed in `.gitignore` and should never be checked in.

Before pushing to GitHub:
1. Verify `.env` is **not** staged: `git status` should not show `.env`
2. Use `.env.example` as a template - copy it to `.env` and fill in your real credentials locally
3. Never hardcode credentials in source files

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd couchbase-ai-ready-pipeline

# Copy the example env file and fill in your credentials
cp .env.example .env
# Edit .env with your Couchbase Capella and Kaggle credentials
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Couchbase collections and indexes

```bash
python scripts/setup_couchbase.py
```

### 4. Load data into Couchbase

The healthcare dataset (55,000 records) is already included in `data/raw/`. No need to download it separately.

```bash
python scripts/load_healthcare_data.py
```

### 5. Deploy the Eventing Function

1. Open Capella -> **Data Tools** -> **Eventing**
2. Click **Add Function**
3. Configure:
   - **Name:** `knowledge_pipeline`
   - **Source Bucket:** `pharma_knowledge`
   - **Source Scope:** `_default`
   - **Source Collection:** `raw_documents`
   - **Metadata Bucket:** `pharma_knowledge`
   - **Metadata Scope:** `storage`
   - **Metadata Collection:** `metadata`
4. Add a **Bucket Binding**:
   - **Alias:** `processed_docs`
   - **Bucket:** `pharma_knowledge`
   - **Scope:** `_default`
   - **Collection:** `processed_documents`
   - **Access:** Read/Write
5. Copy/paste code from `eventing/knowledge_pipeline.js`
6. **Deploy** and **Resume**

### 6. Verify results

Run these queries in the Capella Query Workbench:

```sql
-- Count processed documents
SELECT COUNT(*) as total
FROM `pharma_knowledge`._default.processed_documents;

-- Verify PII redaction
SELECT COUNT(*) as redacted
FROM `pharma_knowledge`._default.processed_documents
WHERE patient.name = "[NAME_REDACTED]";

-- Query by medical condition
SELECT metadata.medical_condition, COUNT(*) as count
FROM `pharma_knowledge`._default.processed_documents
GROUP BY metadata.medical_condition
ORDER BY count DESC
LIMIT 10;
```

## Project Structure

```
couchbase-ai-ready-pipeline/
├── .env.example                   # Template for credentials (safe to commit)
├── .gitignore                     # Ensures .env is not committed
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── QUICKSTART.md                  # Quick start guide
├── DEMO_SCRIPT.md                 # Short demo script
├── COMPLETE_DEMO_WALKTHROUGH.md   # Full demo walkthrough
├── scripts/
│   ├── setup_couchbase.py         # Create collections & indexes
│   ├── test_connection.py         # Test Couchbase connectivity
│   ├── download_kaggle_data.py    # Download healthcare dataset from Kaggle
│   └── load_healthcare_data.py    # Load records into Couchbase
├── eventing/
│   ├── knowledge_pipeline.js      # Eventing function source code
│   └── knowledge_pipeline.json    # Eventing function export config
└── data/
    └── raw/                       # Included healthcare dataset (~5MB)
```

## Dataset

This demo includes the [Healthcare Dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset) from Kaggle (~5MB, already in `data/raw/`), which contains synthetic patient records with names, ages, medical conditions, billing amounts, and more. No separate download is needed.

## Demo Guides

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup instructions
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Condensed 6-8 minute demo script
- **[COMPLETE_DEMO_WALKTHROUGH.md](COMPLETE_DEMO_WALKTHROUGH.md)** - Full 20-25 minute presentation guide

## License

This project is provided as-is for demonstration purposes.
