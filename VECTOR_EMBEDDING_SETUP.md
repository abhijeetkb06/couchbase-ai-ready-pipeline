# Vector Embedding Pipeline Setup Guide

This guide walks you through setting up real-time vector embedding generation using Couchbase Eventing and HuggingFace's BGE model.

---

## Overview

**What This Does:**
- Watches the `processed_documents` collection for new/updated documents
- Builds a `medical_summary` text from patient data
- Calls HuggingFace API to generate 768-dimension vector embedding
- **Updates the SAME document** with the embedding (no data duplication!)

**Architecture - Only 2 Collections:**
```
raw_documents  -->  processed_documents
    |                    |
    |                    +-- PII redacted
    |                    +-- Metadata enriched  
    |                    +-- Vector embeddings   <-- Added by this function
    |
    +-- Original data with PII (for audit/lineage)
```

**Key Point for Demo:** We're NOT creating another copy of the data. The embedding is added to the existing processed document. Single source of truth!

---

## Step 1: Create the Eventing Function

### 1.1 Navigate to Eventing
1. Open Couchbase Capella
2. Go to **Data Tools** → **Eventing**
3. Click **Add Function**

### 1.2 Basic Settings
| Setting | Value |
|---------|-------|
| **Function Name** | `vector_embedding_pipeline` |
| **Description** | Generates vector embeddings for semantic search |

### 1.3 Source Settings (Listen To)
| Setting | Value |
|---------|-------|
| **Bucket** | `pharma_knowledge` |
| **Scope** | `_default` |
| **Collection** | `processed_documents` |

> **Important:** This function listens to `processed_documents` (NOT raw_documents). It runs AFTER the knowledge_pipeline has already processed the data.

### 1.4 Eventing Storage
| Setting | Value |
|---------|-------|
| **Bucket** | `pharma_knowledge` |
| **Scope** | `_default` |
| **Collection** | `_eventing` (or create `eventing_metadata`) |

---

## Step 2: Configure URL Binding (HuggingFace API)

This is the critical step - you need to add a URL alias that the function uses to call HuggingFace.

### 2.1 Add URL Binding
1. In the function settings, find **URL Bindings** section
2. Click **Add URL Binding**
3. Configure:

| Setting | Value |
|---------|-------|
| **Alias** | `hfApi` |
| **URL** | `https://router.huggingface.co/hf-inference/models/BAAI/bge-base-en-v1.5/pipeline/feature-extraction` |
| **Auth Type** | `bearer` |
| **Bearer Key** | `<your-huggingface-api-token>` |

> **Note:** The alias `hfApi` must match exactly what's used in the code: `curl("POST", hfApi, ...)`

---

## Step 3: Configure Bucket Binding

The function needs read-write access to update documents with embeddings **in the same collection**.

### 3.1 Add Bucket Binding
1. In the function settings, find **Bucket Bindings** section
2. Click **Add Bucket Binding**
3. Configure:

| Setting | Value |
|---------|-------|
| **Alias** | `src_bucket` |
| **Bucket** | `pharma_knowledge` |
| **Scope** | `_default` |
| **Collection** | `processed_documents` |
| **Access** | `read and write` |

> **Note:** The alias `src_bucket` must match exactly what's used in the code: `src_bucket[meta.id] = doc`
> 
> **Important:** This points to the SAME collection the function listens to. The function updates documents in place - no data duplication!

---

## Step 4: Add the Function Code

### 4.1 Copy the Code
1. Open the file: `eventing/vector_embedding_pipeline.js`
2. Copy the entire contents
3. Paste into the **Function Code** editor in Capella

### 4.2 Verify the Code
Make sure you see these key elements:
- `function OnUpdate(doc, meta)` - main handler
- `curl("POST", hfApi, ...)` - API call using the URL binding
- `src_bucket[meta.id] = doc` - updates same collection (no duplication!)
- `buildMedicalSummary()` - helper function

---

## Step 5: Deploy the Function

### 5.1 Save and Deploy
1. Click **Save**
2. Click **Deploy**
3. Wait for status to show **Deployed** (green)

### 5.2 Verify Deployment
- Status should show: **Deployed**
- No errors in the deployment log

---

## Step 6: Test with a Single Document

### 6.1 Create a Test Document
Go to **Data Tools** → **Documents** → Select `processed_documents` collection

Create a new document with ID `test::embedding::001`:

```json
{
  "type": "processed_patient_record",
  "patient": {
    "name": "[NAME_REDACTED]",
    "age": 45,
    "gender": "Male"
  },
  "medical": {
    "condition": "Diabetes",
    "admission_type": "Emergency",
    "medication": "Metformin",
    "test_results": "Abnormal",
    "hospital": "City General Hospital"
  },
  "metrics": {
    "age_group": "Adult",
    "billing_category": "High"
  }
}
```

### 6.2 Check the Result
Wait 5-10 seconds, then refresh the document. You should see:

```json
{
  "type": "processed_patient_record",
  "patient": { ... },
  "medical": { ... },
  "metrics": { ... },
  "medical_summary": "Adult patient, male, diagnosed with Diabetes, emergency admission, prescribed Metformin, test results abnormal, at City General Hospital, high cost case",
  "embedding": [0.0234, -0.0156, 0.0412, ... ],  // 768 numbers
  "embedding_status": "success",
  "embedding_generated_at": "2024-01-21T10:30:00.000Z",
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "embedding_dimensions": 768
}
```

### 6.3 Check Eventing Logs
If the embedding doesn't appear:
1. Go to **Eventing** → Click on function name
2. Click **Log** tab
3. Look for error messages

Common issues:
- `hfApi is not defined` → URL binding alias is wrong
- `dst_bucket is not defined` → Bucket binding alias is wrong
- `401 Unauthorized` → Bearer token is incorrect
- `503 Service Unavailable` → HuggingFace rate limit, wait and retry

---

## Step 7: Trigger Embeddings for Existing Documents

The eventing function only triggers on document changes. To generate embeddings for existing processed documents, you need to "touch" them.

### Option A: Query Workbench (Small Batches)
Run this query to trigger the first 100 documents:

```sql
UPDATE `pharma_knowledge`._default.processed_documents
SET triggered_at = NOW_STR()
WHERE type = "processed_patient_record"
  AND embedding IS MISSING
LIMIT 100;
```

Repeat with different LIMIT values or run multiple times.

### Option B: Python Script (Recommended for 55,000 docs)
Use the provided script: `scripts/trigger_embeddings.py`

---

## Step 8: Verify Embeddings at Scale

### 8.1 Count Documents with Embeddings
```sql
SELECT COUNT(*) as with_embedding
FROM `pharma_knowledge`._default.processed_documents
WHERE embedding IS NOT MISSING;
```

### 8.2 Count Documents Without Embeddings
```sql
SELECT COUNT(*) as without_embedding
FROM `pharma_knowledge`._default.processed_documents
WHERE embedding IS MISSING
  AND type = "processed_patient_record";
```

### 8.3 Check Embedding Quality
```sql
SELECT 
    META().id,
    medical_summary,
    embedding_status,
    embedding_dimensions,
    ARRAY_LENGTH(embedding) as actual_dimensions
FROM `pharma_knowledge`._default.processed_documents
WHERE embedding IS NOT MISSING
LIMIT 5;
```

---

## Step 9: Create Composite Vector Index

Once you have embeddings, create the composite vector index:

```sql
CREATE INDEX idx_patient_vector ON `pharma_knowledge`._default.processed_documents(
    embedding VECTOR,
    metrics.age_group,
    metrics.billing_category,
    medical.condition
)
WITH {
    "dimension": 768,
    "similarity": "DOT",
    "description": "IVF,SQ8"
};
```

---

## Step 10: Run Semantic Search Queries

### Find Similar Patients (Vector Search)
First, get an embedding for your query text, then search:

```sql
SELECT 
    META().id,
    medical.condition,
    metrics.age_group,
    metrics.billing_category,
    medical_summary
FROM `pharma_knowledge`._default.processed_documents
WHERE embedding IS NOT MISSING
ORDER BY APPROX_VECTOR_DISTANCE(embedding, $query_vector, "DOT")
LIMIT 10;
```

### Hybrid Search: Vector + Filters
```sql
SELECT 
    META().id,
    medical.condition,
    metrics.age_group,
    metrics.billing_category
FROM `pharma_knowledge`._default.processed_documents
WHERE metrics.billing_category = "High"
  AND embedding IS NOT MISSING
ORDER BY APPROX_VECTOR_DISTANCE(embedding, $query_vector, "DOT")
LIMIT 10;
```

---

## Troubleshooting

### Problem: Embedding not appearing
1. Check eventing function is **Deployed** (green status)
2. Check **Logs** for errors
3. Verify URL binding alias is exactly `hfApi`
4. Verify bucket binding alias is exactly `src_bucket`

### Problem: 401 Unauthorized
- Bearer token may have expired
- Update the URL binding with new token

### Problem: Rate Limiting (429 or 503)
- HuggingFace free tier has limits
- Add delays between document triggers
- Consider upgrading HuggingFace plan for high volume

### Problem: Function not triggering
- Document must have `type: "processed_patient_record"`
- Document must NOT already have `embedding` field
- Try updating a field to trigger OnUpdate

---

## Summary

You now have:
1. **Real-time embedding generation** - Every new processed document gets an embedding automatically
2. **Medical summary field** - Human-readable text that was embedded
3. **768-dimension vectors** - Ready for semantic search
4. **Composite vector index** - Enables hybrid search (vector + filters)

This transforms your demo from "data preparation" to "AI-ready data with semantic search capabilities"!
