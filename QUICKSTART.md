# Simplified Architecture - Quick Start Guide


**NOW (Simple):**
- 1 scope (`_default`), 3 collections
- 1 eventing function (single pipeline)
- 10,000 real healthcare records
- Clear, impactful demo story

---

## Architecture Overview

```
pharma_knowledge (bucket)
└── _default (scope)
    ├── raw_documents          ← Data lands here with PII
    ├── processed_documents    ← Clean, enriched data
    └── metadata               ← Eventing state/checkpoints
    
                ↓ Eventing Function ↓
         [Redact → Enrich → Write]
```

---

## Setup Steps

### 1. Delete Old Structure (if needed)

If you already ran the old setup, delete all scopes/collections in Capella UI except the bucket.

### 2. Run Simplified Setup

```bash
python scripts/setup_couchbase.py
```

Creates:
- `raw_documents` collection
- `processed_documents` collection
- Indexes for querying

### 3. Download Healthcare Dataset

```bash
# Install Kaggle CLI
pip install kaggle

# Set up Kaggle API credentials
# Go to https://www.kaggle.com/account → Create API Token
# Save to ~/.kaggle/kaggle.json

# Download dataset (10,000 patient records)
python scripts/download_kaggle_data.py
```

### 4. Load Data into Couchbase

```bash
python scripts/load_healthcare_data.py
```

Loads 10,000 patient records with:
- Names (PII - will be redacted)
- Medical conditions
- Doctors, hospitals
- Billing information

### 5. Deploy Eventing Function

1. Open Capella → **Data Tools** → **Eventing**
2. Click **Add Function**
3. Configure:
   - **Name:** `knowledge_pipeline`
   - **Source Bucket:** `pharma_knowledge`
   - **Source Scope:** `_default`
   - **Source Collection:** `raw_documents`
   - **Metadata Bucket:** `pharma_knowledge`
   - **Metadata Scope:** `_default`
   - **Metadata Collection:** `metadata` (Important: Must be a dedicated collection)
4. **Bucket Bindings** (Critical!):
   - Click "Add Binding"
   - **Alias:** `processed_docs`
   - **Bucket:** `pharma_knowledge`
   - **Scope:** `_default`
   - **Collection:** `processed_documents`
   - **Access:** Read/Write
5. **Code:** Copy/paste from `eventing/knowledge_pipeline.js`
6. Click **Deploy**
7. Click **Resume**

### 6. Watch the Pipeline

Monitor processing:
- Capella → Eventing → `knowledge_pipeline`
- See documents processed in real-time
- ~50-100 docs/second
- Complete in 2-3 minutes

### 7. Verify Results

```sql
-- Count processed documents
SELECT COUNT(*) as total
FROM `pharma_knowledge`._default.processed_documents

-- Verify PII redaction
SELECT COUNT(*) as redacted
FROM `pharma_knowledge`._default.processed_documents
WHERE patient.name = "[NAME_REDACTED]"

-- Query by medical condition
SELECT metadata.medical_condition, COUNT(*) as count
FROM `pharma_knowledge`._default.processed_documents
GROUP BY metadata.medical_condition
ORDER BY count DESC
LIMIT 10
```

### 8. Run Demo

Follow `DEMO_SCRIPT.md` for the complete walkthrough.

---

## Demo Story

**The Problem:**
- 10,000 patient records just landed
- Every one has PII (patient names)
- Unstructured metadata
- Can't be indexed as-is

**The Solution:**
- ONE eventing function watches for new data
- Automatically redacts PII
- Enriches metadata
- Writes clean output
- All in real-time, at scale

**The Impact:**
- 3 minutes to process 10,000 records
- Zero ETL jobs
- Zero manual cleanup
- Ready for AI/search immediately

---

## File Structure

```
couchbase-ai-ready-pipeline/
├── .env                           # Your credentials
├── requirements.txt               # Python dependencies
├── QUICKSTART.md                  # This file
├── DEMO_SCRIPT.md                 # Complete demo walkthrough
├── scripts/
│   ├── setup_couchbase.py        # Create collections & indexes
│   ├── download_kaggle_data.py   # Download 10K records
│   └── load_healthcare_data.py   # Load into Couchbase
└── eventing/
    └── knowledge_pipeline.js      # Single eventing function
```

---

## Troubleshooting

### "Kaggle API credentials not found"
1. Go to https://www.kaggle.com/account
2. Scroll to API section
3. Click "Create New API Token"
4. Save to `~/.kaggle/kaggle.json`
5. Run: `chmod 600 ~/.kaggle/kaggle.json`

### "Eventing function not processing"
- Check function is **Deployed** and **Running**
- Check bucket binding is configured
- View logs: Click function → Logs tab
- Verify documents have `processing_status: "pending"`

### "No documents in processed_documents"
- Wait 2-3 minutes for processing
- Check eventing function logs for errors
- Verify bucket binding alias is `processed_docs`
- Ensure binding has Read/Write access

---

## Key Demo Queries

```sql
-- Show scale
SELECT COUNT(*) FROM raw_documents;
SELECT COUNT(*) FROM processed_documents;

-- Verify PII redaction (should return 10,000)
SELECT COUNT(*) FROM processed_documents
WHERE patient.name = "[NAME_REDACTED]";

-- Query enriched metadata
SELECT 
  metadata.medical_condition,
  metrics.age_group,
  COUNT(*) as patients
FROM processed_documents
GROUP BY metadata.medical_condition, metrics.age_group
ORDER BY patients DESC
LIMIT 20;

-- Find high-risk cases
SELECT 
  patient.age,
  medical.condition,
  billing.amount,
  metrics.billing_category
FROM processed_documents
WHERE metrics.billing_category IN ["High", "Very High"]
  AND metrics.age_group IN ["Senior", "Elderly"]
LIMIT 10;
```

---

**This is the Knowledge Preparation Layer at scale.**
