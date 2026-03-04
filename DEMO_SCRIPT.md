# Simplified Demo Script - Knowledge Preparation Layer at Scale

**Duration:** 6-8 minutes  
**Audience:** Technical Decision Makers  
**Key Message:** "The hard part isn't retrieval - it's making data retrieval-ready at scale."

---

## Pre-Demo Checklist

- [x] Couchbase Capella cluster running
- [x] Bucket `pharma_knowledge` exists
- [x] 55,000 patient records loaded into `raw_documents`
- [x] Eventing function `knowledge_pipeline` deployed and running
- [x] Browser tabs open:
  - Tab 1: Capella → Documents (raw_documents)
  - Tab 2: Capella → Documents (processed_documents)
  - Tab 3: Capella → Eventing (function dashboard)
  - Tab 4: Capella → Query Workbench

---

## OPENING (30 seconds)

> RAG is becoming commoditizedEveryone can embed documents and run vector search now.
>
> But here's the problem nobody talks about: **What happens BEFORE you can retrieve?**
>
> Let me show you with real healthcare data - 55,000 patient records that just landed in our system. Every one has PII that can't be indexed, messy metadata, and inconsistent formatting.
>
> Watch what happens automatically."

---

## ACT 1: THE PROBLEM (1 minute)

### Show Raw Data with PII

**Navigate to:** Capella → Documents → `raw_documents`

**Open any document, point to:**

```json
{
  "_id": "patient::john_smith::1847",
  "name": "John Smith",  // ← PII PROBLEM
  "medical_condition": "Diabetes",
  "doctor": "Dr. Sarah Johnson",
  "billing_amount": 25432.50,
  "processing_status": "pending"
}
```

> "See the problem? This is real patient data. We have:
> - **Patient names** - can't index this, HIPAA violation
> - **Unstructured metadata** - can't filter by condition type
> - **55,000 of these** landing right now
>
> In most systems, someone has to manually clean this up. Or you write custom ETL jobs.
>
> Not here. Watch."

---

## ACT 2: THE TRANSFORMATION (2-3 minutes)

### Show Eventing Function Processing

**Navigate to:** Capella → Eventing → `knowledge_pipeline`

> "We have ONE eventing function watching for new documents. When it sees `processing_status: 'pending'`, it automatically:
> 1. Redacts PII
> 2. Enriches metadata
> 3. Writes to processed collection
>
> All in real-time, at the data layer."

**Show the function dashboard:**
- Processed: ~55,000 documents
- Rate: ~50-100 docs/sec
- Status: Running

> "This is processing all 55,000 records right now. Takes about 10-15 minutes."

---

### Show Processed Data

**Navigate to:** Capella → Documents → `processed_documents`

**Open a processed document:**

```json
{
  "_id": "processed::john_smith::1847",
  "patient": {
    "name": "[NAME_REDACTED]",  // ← PII REMOVED
    "age": 45,
    "gender": "Male"
  },
  "medical": {
    "condition": "Diabetes",
    "doctor": "Dr. Sarah Johnson",
    "hospital": "General Hospital"
  },
  "metadata": {
    "medical_condition": "Diabetes",  // ← STRUCTURED
    "admission_type": "Emergency",
    "doctor": "Dr. Sarah Johnson"
  },
  "metrics": {
    "age_group": "Adult",  // ← ENRICHED
    "billing_category": "Medium"
  },
  "pii_redaction": {
    "pii_found": ["name"],
    "redacted_at": "2024-01-18T12:30:00Z"
  },
  "is_pii_compliant": true
}
```

> "Same record. But look:
> - **Name redacted** - PII compliant
> - **Metadata structured** - ready for filtering
> - **Metrics added** - age group, billing category
> - **Audit trail** - we know what was redacted and when
>
> This is now READY for retrieval. Your AI teams can query it, embed it, search it - safely."

---

## ACT 3: PROOF AT SCALE (2 minutes)

### Query the Results

**Navigate to:** Capella → Query Workbench

**Query 1: Verify PII redaction worked**

```sql
SELECT COUNT(*) as total_redacted
FROM `pharma_knowledge`._default.processed_documents
WHERE patient.name = "[NAME_REDACTED]"
```

> "Result: 55,000. Every single patient name was redacted automatically."

---

**Query 2: Query by enriched metadata**

```sql
SELECT metadata.medical_condition, COUNT(*) as count
FROM `pharma_knowledge`._default.processed_documents
GROUP BY metadata.medical_condition
ORDER BY count DESC
LIMIT 10
```

> "Now I can query by medical condition - something I couldn't do with the raw data. This metadata was EXTRACTED and STRUCTURED automatically."

---

**Query 3: Find high-risk patients**

```sql
SELECT patient.age, medical.condition, billing.amount
FROM `pharma_knowledge`._default.processed_documents
WHERE metrics.billing_category = "Very High"
  AND metrics.age_group IN ["Senior", "Elderly"]
LIMIT 10
```

> "Complex business query - high-cost elderly patients. This works because the data was PREPARED for this kind of analysis."

---

## CLOSING (30 seconds)

> "Here's what just happened:
>
> **55,000 patient records landed in our system.**  
> **Every one had PII, messy metadata, inconsistent structure.**  
> **Within 15 minutes, all 55,000 were:**
> -  PII redacted (HIPAA compliant)
> - Metadata enriched (queryable, filterable)
> - Audit trail captured (governance)
> - Ready for retrieval (AI teams can use immediately)
>
> **Zero ETL jobs. Zero manual cleanup. Zero custom code.**
>
> This is the Knowledge Preparation Layer.  
> OpenSearch can't do this. Pinecone can't do this. ElasticSearch can't do this.
>
> This is what happens BEFORE retrieval - and it's the hard part."

---

---

## Quick Reference

### Documents to Show
- Raw: `patient::*` (any in raw_documents)
- Processed: `processed::*` (any in processed_documents)

### Key Queries
```sql
-- Count processed
SELECT COUNT(*) FROM processed_documents

-- PII check
SELECT * FROM processed_documents 
WHERE patient.name != "[NAME_REDACTED]"
-- Should return 0

-- Metadata query
SELECT metadata.medical_condition, COUNT(*) 
FROM processed_documents 
GROUP BY metadata.medical_condition
```

---

**Last updated:** January 2024  
**Demo version:** 2.0 (Simplified)
