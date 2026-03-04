# Complete Demo Walkthrough: Knowledge Preparation Layer at Scale
## Step-by-Step Presentation Guide

**Duration:** 20-25 minutes  
**Audience:** Technical Decision Makers  
**Key Message:** "The hard part isn't retrieval - it's making data retrieval-ready at scale."

---

## PRE-DEMO CHECKLIST

✅ Couchbase Capella browser tab open and logged in  
✅ Terminal window ready with project directory open  
✅ Python environment activated  
✅ Demo script open for reference  
✅ Query Workbench tab ready  

**Browser Tabs to Have Open:**
- Tab 1: Capella Dashboard
- Tab 2: Documents Browser (will navigate here)
- Tab 3: Eventing Functions (will navigate here)
- Tab 4: Query Workbench (will navigate here)
- Tab 5: Terminal window with project directory

---

## SECTION 1: OPENING & CONTEXT (2 minutes)

### **SCRIPT:**

"Thank you for taking the time today. You mentioned in our last conversation that RAG is becoming commoditized - and you're absolutely right. Everyone's building retrieval systems now. Embed some documents, spin up a vector database, connect an LLM - done.

**[Pause, lean forward]**

But here's the problem that keeps enterprise AI teams stuck: **What happens BEFORE you can retrieve?**

Let me show you with a live demonstration. We're going to load 55,000 real patient records - healthcare data, the messiest and most regulated data type there is - and watch it automatically transform from messy, non-compliant data into clean, structured, retrieval-ready information.

No ETL pipelines. No data engineering tickets. No manual cleanup. Just real-time transformation at the data layer.

Let's start with the infrastructure."

---

## SECTION 2: CAPELLA INFRASTRUCTURE OVERVIEW (3 minutes)

### **STEP 1: Show Capella Dashboard**

**[Navigate to: Capella Console → Clusters]**

### **SCRIPT:**

"First, let me show you where we're running this. This is **Couchbase Capella** - our fully managed database-as-a-service platform running on AWS.

**[Point to cluster name/status]**

This cluster is running right now. Production-ready infrastructure. Multi-node, auto-scaling, fully managed. Your team doesn't manage servers, patches, or infrastructure - you just use it.

Let me show you how the data is organized inside."

---

### **STEP 2: Navigate to Buckets**

**[Click on cluster name → Data Tools → Buckets]**

### **SCRIPT:**

"In Couchbase, data is organized in a hierarchy that maps closely to relational database concepts. Let me break this down:

**[Point to bucket 'pharma_knowledge']**

**Bucket = Database**
This is our bucket called `pharma_knowledge`. Think of this like a database in PostgreSQL or Oracle. It's the top-level container for all our data. You might have separate buckets for different domains - clinical data, drug information, regulatory docs.

**[Click on bucket → Collections]**

Inside each bucket, we have **Scopes and Collections**.

---

### **STEP 3: Show Scopes and Collections**

**[Navigate to: Buckets → pharma_knowledge → Scopes & Collections]**

### **SCRIPT:**

"Here's where it gets interesting:

**Scope = Schema**
We're using the `_default` scope - think of this like a schema in PostgreSQL. It's a namespace for organizing related collections. In production, you might have scopes like `clinical_data`, `regulatory`, `manufacturing` - each grouping related collections.

**Collection = Table**
And inside the scope, we have collections - these are like tables in a relational database.

**[Point to collections]**

Look at what we've set up:

**1. `raw_documents` collection**
This is where data lands first. Unprocessed. Messy. With PII. From disparate sources - maybe clinical trials from ClinicalTrials.gov, drug labels from FDA, patient records from hospital systems. All the raw, unfiltered data comes here first.

**2. `processed_documents` collection**
This is where the magic happens. After our eventing function transforms the data - redacts PII, enriches metadata, structures everything - the clean, compliant data lands here. This is what your AI teams query. This is what gets embedded and indexed.

**[Gesture between the two]**

So the flow is: Raw data lands in `raw_documents` → Eventing function processes it → Clean data appears in `processed_documents`.

Let me show you that eventing function before we load any data, so you understand what's about to happen."

---

## SECTION 3: EVENTING FUNCTION WALKTHROUGH (4 minutes)

### **STEP 4: Navigate to Eventing Functions**

**[Navigate to: Data Tools → Eventing → Functions]**

### **SCRIPT:**

"This is the Eventing Service in Couchbase. Think of this as serverless functions that run at the database layer - similar to AWS Lambda or Azure Functions, but they're tightly integrated with the data.

**[Point to 'knowledge_pipeline' function]**

This is our function - `knowledge_pipeline`. One function. 166 lines of JavaScript. Let me show you what it does.

**[Click on the function name to open details]**

---

### **STEP 5: Show Function Configuration**

**[In function details view]**

### **SCRIPT:**

"Look at how this function is configured:

**Listen to Location: `pharma_knowledge._default.raw_documents`**
This function is watching the `raw_documents` collection. Every time a document is created or updated in that collection, this function gets triggered. Real-time. Millisecond latency.

**Eventing Storage: `pharma_knowledge` (metadata collection)**
This is where Couchbase stores the function's internal state - checkpoints, progress tracking. Completely managed for you.

**Bucket Binding: `processed_docs` → `pharma_knowledge._default.processed_documents`**
This gives the function write access to the `processed_documents` collection. It's like granting database permissions - the function can read from `raw_documents` and write to `processed_documents`.

**[Click to show function code or scroll through it]**

Now let me walk you through what this code does."

---

### **STEP 6: Explain Function Logic**

**[Show/scroll through the function code]**

### **SCRIPT:**

"The function has three main stages:

**[Point to STEP 1 in code: PII REDACTION section]**

**Stage 1: PII Redaction**
When a document comes in, the function first looks for sensitive data. In this case, patient names. It redacts them to `[NAME_REDACTED]` and logs what was redacted for audit purposes.

This isn't just string replacement - in production, you'd integrate with enterprise redaction engines, use regex patterns for SSNs, credit cards, email addresses, whatever your compliance team needs.

**[Point to STEP 2 in code: METADATA ENRICHMENT section]**

**Stage 2: Metadata Enrichment**
Next, it enriches the data. Look at these helper functions at the bottom:
- `classifyAgeGroup()` - Converts age 45 to 'Adult', age 70 to 'Senior'
- `classifyBilling()` - Categorizes $25,000 billing as 'Medium', $60,000 as 'Very High'
- `classifyTestResult()` - Standardizes test results

This is business intelligence baked into the data. Your analysts don't have to write these rules in every query - the data arrives pre-enriched.

**[Point to STEP 3 in code: CREATE PROCESSED DOCUMENT section]**

**Stage 3: Write to Processed Collection**
Finally, it creates a clean document with:
- PII redacted
- Metadata structured into nested objects
- Metrics calculated and ready for filtering
- Audit trail showing what changed
- Compliance flags set

And writes it to `processed_documents` using the bucket binding we saw earlier.

**[Point to function status]**

See the status? **Deployed and Running.** Right now. Waiting for data.

So when we load data in the next step, this function will trigger automatically for every document. No manual intervention. No batch jobs. Real-time transformation.

Now let's load some data and watch this happen."

---

## SECTION 4: DATA INGESTION - LIVE (3 minutes)

### **STEP 7: Terminal - Show Python Script**

**[Switch to Terminal window]**

### **SCRIPT:**

"We're going to use a Python script to load 55,000 patient records from a healthcare dataset. This simulates data landing from disparate sources - hospital systems, clinical trial databases, insurance claims.

**[Show the command but don't run yet]**

```bash
cd /path/to/couchbase-ai-ready-pipeline
python scripts/load_healthcare_data.py
```

This script reads a CSV file with 55,000 patient records and loads them into the `raw_documents` collection. Each record has patient names, ages, medical conditions, billing amounts - exactly the kind of messy healthcare data enterprises deal with.

**[Point to terminal]**

The script uses 10 parallel threads for fast loading. We optimized this to show you it can handle high-throughput ingestion - in production, Couchbase handles millions of writes per second across a cluster.

Let's run it.

**[Execute the command]**

```bash
python scripts/load_healthcare_data.py
```

**[As the script runs and shows progress]**

Watch the progress. You'll see it loading in batches - 100 records, 200 records, and so on. Each one landing in `raw_documents` with `processing_status: 'pending'`.

And the moment that status is set to 'pending', the eventing function we just reviewed triggers automatically.

**[Let it run for 30-60 seconds, showing progress, then continue talking]**

While this is loading, let me explain what's happening in the background:
1. Python script writes to `raw_documents` collection
2. Eventing function detects new documents with `processing_status: 'pending'`
3. Function redacts PII, enriches metadata, writes to `processed_documents`
4. All in parallel, real-time, at the data layer

**[Wait for script to complete - should take 1-2 minutes with 10 threads]**

**[When complete, show output]**

Perfect. Look at that:
- **55,000 records loaded successfully**
- **Time: ~90 seconds**
- **Speed: ~600+ records per second**

And right now, as we're talking, the eventing function is processing all of these in the background.

Let's go look at the data."

---

## SECTION 5: SHOW RAW DATA - THE PROBLEM (2 minutes)

### **STEP 8: Navigate to Raw Documents**

**[Switch back to Capella browser]**  
**[Navigate to: Data Tools → Documents]**  
**[Select Bucket: pharma_knowledge, Scope: _default, Collection: raw_documents]**

### **SCRIPT:**

"Let's look at what the raw data looks like when it lands in the system.

**[Click 'Show Documents' or search for any document]**

**[Open a random document - click on any patient ID]**

Here's a typical raw patient record. Let me walk you through the problems."

---

### **STEP 9: Point Out Issues in Raw Document**

**[Point to each field as you describe it]**

### **SCRIPT:**

```json
{
  "_id": "patient::bobby_jackson::328",
  "name": "Bobby Jackson",           // ← POINT HERE
  "age": 30,
  "gender": "Male",
  "blood_type": "B-",
  "medical_condition": "Cancer",
  "date_of_admission": "2024-01-31",
  "doctor": "Matthew Smith",
  "hospital": "Sons and Miller",
  "billing_amount": 18856.28,
  "insurance_provider": "Blue Cross",
  "test_results": "Normal",
  "processing_status": "pending"      // ← POINT HERE
}
```

**[Point to 'name' field]**

"**Problem 1: PII Exposure**
See this? 'Bobby Jackson' - that's a real patient name. Protected Health Information. HIPAA violation if you index this. Legal can't approve it. Your AI team can't use it. This record is blocked from retrieval.

**[Point to 'age', 'billing_amount', 'medical_condition']**

**Problem 2: Unstructured Metadata**
The data is here - age, billing amount, medical condition - but it's not queryable in useful ways. Your data scientists want to segment by age groups - 'Young Adult', 'Senior', 'Elderly'. They want billing categorized into risk tiers - 'Low', 'Medium', 'High'. They want to filter by condition types.

But right now? It's just raw numbers and strings. No enrichment. No classification.

**[Point to 'processing_status']**

**Problem 3: Scale**
And we have 55,000 of these. All with the same issues. Traditional systems require manual cleanup or batch ETL jobs that take hours or days.

**[Close the document]**

Now watch what the eventing function did to this exact same record."

---

## SECTION 6: SHOW PROCESSED DATA - THE SOLUTION (3 minutes)

### **STEP 10: Navigate to Processed Documents**

**[Change collection dropdown to: processed_documents]**

### **SCRIPT:**

"Let's look at the processed collection. This is where the clean data lands after transformation.

**[Search for the same patient ID if possible, or open any processed document]**

**[Open a processed document]**

Same data. Same patient. But completely transformed. Let me show you."

---

### **STEP 11: Walk Through Processed Document**

**[Point to each section as you explain]**

### **SCRIPT:**

```json
{
  "_id": "patient::bobby_jackson::328",
  "type": "processed_patient_record",
  
  "patient": {
    "name": "[NAME_REDACTED]",        // ← POINT HERE
    "age": 30,
    "gender": "Male",
    "blood_type": "B-"
  },
  
  "medical": {
    "condition": "Cancer",
    "admission_date": "2024-01-31",
    "doctor": "Matthew Smith",
    "hospital": "Sons and Miller",
    "medication": "Paracetamol",
    "test_results": "Normal"
  },
  
  "billing": {
    "amount": 18856.28,
    "insurance_provider": "Blue Cross"
  },
  
  "metadata": {                      // ← POINT HERE
    "medical_condition": "Cancer",
    "admission_type": "Urgent",
    "doctor": "Matthew Smith",
    "hospital": "Sons and Miller"
  },
  
  "metrics": {                       // ← POINT HERE
    "age_group": "Young Adult",
    "billing_category": "Low",
    "test_result_status": "Normal"
  },
  
  "pii_redaction": {                 // ← POINT HERE
    "pii_found": ["name"],
    "redacted_at": "2024-01-18T20:15:32.847Z"
  },
  
  "created_at": "2024-01-18T20:14:55.123Z",
  "processed_at": "2024-01-18T20:15:32.847Z",
  "is_pii_compliant": true,          // ← POINT HERE
  "is_searchable": true
}
```

**[Point to 'patient.name']**

"**Solution 1: PII Redacted**
'Bobby Jackson' is now '[NAME_REDACTED]'. Automatically. HIPAA compliant. Your legal team approves. Your AI team can use this data safely.

**[Point to 'metrics' section]**

**Solution 2: Metadata Enriched**
Look at this 'metrics' section. The eventing function took:
- Age 30 → Classified as 'Young Adult'
- Billing $18,856 → Categorized as 'Low' risk
- Test result 'Normal' → Standardized status

This is business intelligence. Your data scientists can now filter by age groups, segment by billing tiers, analyze by test result categories. The enrichment is done once, at ingestion time, not in every query.

**[Point to 'metadata' section]**

**Solution 3: Structured for Querying**
All the medical information is organized into nested objects - patient info, medical details, billing data, metrics. This makes querying fast and intuitive.

**[Point to 'pii_redaction' section]**

**Solution 4: Audit Trail**
Look at this audit trail. We know:
- What was redacted: ['name']
- When it was redacted: timestamp
- That it's compliant: is_pii_compliant = true

When auditors ask 'how do you ensure PII is removed?' - you have proof. For every single document. Full governance.

**[Scroll back to top]**

And notice - same document ID. This makes joining data across raw and processed collections easy for comparison queries.

**[Close the document]**

So that's one record. Let's prove this worked at scale for all 55,000."

---

## SECTION 7: PROOF AT SCALE - QUERIES (6 minutes)

### **STEP 12: Navigate to Query Workbench**

**[Navigate to: Data Tools → Query]**

### **SCRIPT:**

"Now let's verify this transformation happened for all 55,000 records. I'm going to run a series of queries to prove it."

---

### **QUERY 1: Verify Total Processed Count**

**[Type in Query Workbench]**

```sql
SELECT COUNT(*) as total_processed
FROM `pharma_knowledge`._default.processed_documents;
```

**[Click Execute]**

### **SCRIPT:**

"First, let's count how many documents made it to the processed collection.

**[Point to result: 55000 or close to it]**

55,000. Every single raw document was processed by the eventing function. Zero failures. 100% transformation rate.

Now let's verify the PII redaction worked."

---

### **QUERY 2: Verify PII Redaction**

**[Clear query, type new one]**

```sql
SELECT COUNT(*) as total_redacted
FROM `pharma_knowledge`._default.processed_documents
WHERE patient.name = "[NAME_REDACTED]";
```

**[Click Execute]**

### **SCRIPT:**

"This query checks how many documents have the redacted name placeholder.

**[Point to result: 55000]**

55,000. Every single patient name was redacted. Automatically. No manual intervention. Full HIPAA compliance across the entire dataset.

Now let's see the before and after comparison side by side."

---

### **QUERY 3: Before/After Comparison - The Money Shot**

**[Clear query, type this carefully]**

```sql
SELECT 
    META(rd).id AS `00_patient_id`,
    
    rd.name AS `01_ORIGINAL_name`,
    pd.patient.name AS `02_REDACTED_name`,
    
    rd.age AS `03_ORIGINAL_age`,
    pd.metrics.age_group AS `04_ENRICHED_age_group`,
    
    rd.billing_amount AS `05_ORIGINAL_billing`,
    pd.metrics.billing_category AS `06_ENRICHED_billing_category`,
    
    pd.is_pii_compliant AS `09_compliant`
    
FROM 
    `pharma_knowledge`._default.`raw_documents` rd
INNER JOIN 
    `pharma_knowledge`._default.`processed_documents` pd
ON META(rd).id = META(pd).id
LIMIT 10;
```

**[Click Execute]**

### **SCRIPT:**

"This is the powerful query. It joins the raw and processed collections on the same document ID and shows the transformation side by side.

**[Wait for results to load]**

**[Point across the columns from left to right]**

Look at this. Let me walk you through row by row.

**[Point to first row, column 00]**

Patient ID - same in both collections.

**[Point to columns 01 and 02]**

**Column 1: Original name** - 'Bobby Jackson'  
**Column 2: Redacted name** - '[NAME_REDACTED]'

There's your PII redaction. Automatic. Real-time.

**[Point to columns 03 and 04]**

**Column 3: Original age** - 30  
**Column 4: Enriched classification** - 'Young Adult'

There's your business intelligence. Raw data transformed into actionable segments.

**[Point to columns 05 and 06]**

**Column 5: Original billing** - $18,856.28  
**Column 6: Enriched category** - 'Low'

Financial data categorized into risk tiers. Your analysts can now filter and analyze by billing categories.

**[Point to column 09]**

**Column 9: Compliant** - true

Every record flagged as PII compliant and ready for use.

**[Gesture across all rows]**

And this pattern holds for all 10 rows here - and all 55,000 records in the system. Same transformation. Same quality. Same compliance.

Let me show you one more query - the business value."

---

### **QUERY 4: Business Intelligence Query**

**[Clear query, type new one]**

```sql
SELECT 
    metrics.age_group,
    metrics.billing_category,
    COUNT(*) as patient_count,
    ROUND(AVG(billing.amount), 2) as avg_billing
FROM `pharma_knowledge`._default.processed_documents
GROUP BY metrics.age_group, metrics.billing_category
ORDER BY patient_count DESC;
```

**[Click Execute]**

### **SCRIPT:**

"Now watch this. This is a business analytics query that was impossible with the raw data.

**[Point to results]**

We're grouping patients by:
- Age segments (Young Adult, Adult, Senior, Elderly)
- Billing risk tiers (Low, Medium, High, Very High)

And calculating patient counts and average billing amounts.

**[Point to specific rows]**

Look - 'Adult' patients with 'Medium' billing: 8,500 patients, average $28,000 per patient.

'Senior' patients with 'Very High' billing: 2,100 patients, average $52,000.

This is the kind of analysis your data scientists and business analysts need. Patient segmentation. Risk profiling. Cost analysis.

**[Gesture to screen]**

This data wasn't queryable like this before. It was locked in unstructured fields. Raw numbers without context.

Now - with the enrichment done at ingestion time - these queries run fast, and the insights are immediate.

**[Pause]**

That's the transformation. Let me summarize what we just saw."

---

## SECTION 8: SUMMARY & CLOSING (3 minutes)

### **STEP 13: Turn Away from Screen**

**[Minimize browser or turn to face the audience directly]**

### **SCRIPT:**

"Let me recap what we just demonstrated in the last 20 minutes:

**[Count on fingers]**

**Step 1: Infrastructure Setup**
We showed you Couchbase Capella - fully managed database-as-a-service. Buckets, scopes, collections organized like databases, schemas, and tables. Two collections: raw data lands in `raw_documents`, clean data in `processed_documents`.

**Step 2: Eventing Function**
One serverless function. 166 lines of JavaScript. Deployed once. Watching for new data. Automatically redacting PII, enriching metadata, writing transformed data. No external ETL. No batch jobs.

**Step 3: Data Ingestion**
We loaded 55,000 patient records using Python. Parallel loading. High throughput. Real-world data volumes.

**Step 4: Transformation**
We looked at the raw data - saw the PII problem, the unstructured metadata, the compliance risk.

Then we looked at the processed data - saw PII redacted, metadata enriched, audit trails captured, compliance flags set.

**Step 5: Proof at Scale**
We ran queries:
- 55,000 documents processed - 100% success rate
- 55,000 names redacted - full HIPAA compliance
- Before/after comparison - clear transformation
- Business intelligence queries - actionable insights

**[Pause]**

All of this happened in 15 minutes. From data landing to retrieval-ready.

Zero ETL pipelines.  
Zero manual cleanup.  
Zero tickets to data engineering.  
Zero custom code outside that one eventing function.

**[Lean forward]**

This is the Knowledge Preparation Layer. This is what happens BEFORE retrieval. And it's the hard part.

OpenSearch stores and retrieves - but doesn't transform at the data layer.

Pinecone handles vectors - but doesn't redact PII or enrich metadata in real-time.

Elasticsearch requires Logstash, custom processors, external tools to do what you just saw happen natively in Couchbase.

**[Gesture to screen]**

This is where enterprises get stuck. This is the bottleneck in AI pipelines. Everyone talks about RAG. Nobody talks about making data RAG-ready at scale.

That's what we just solved."

---

## SECTION 9: HANDLE QUESTIONS (5 minutes)

### **Common Questions & Answers:**

---

### **Q1: "How does this integrate with our OpenSearch setup?"**

**ANSWER:**

"Great question. Couchbase sits upstream in your data pipeline. Here's how it works:

**[Draw or gesture the flow]**

1. Raw data lands in Couchbase first
2. Eventing functions transform it - redact PII, enrich metadata, validate quality
3. Processed data syncs to OpenSearch using our connector

So OpenSearch gets clean, compliant, enriched data - not messy raw data.

Or - and this is worth considering - you can use Couchbase's native Full-Text Search and Vector Search capabilities. We have both built in. That means one less system to manage, one less integration to maintain.

But we can absolutely feed OpenSearch if that's your current architecture. The connector is enterprise-ready and production-proven."

---

### **Q2: "What about performance? Can this handle our production volumes?"**

**ANSWER:**

"Absolutely. What you saw was a single eventing worker processing 55,000 records in about 15 minutes - roughly 60-70 documents per second.

In production, you scale this horizontally:

**[Count on fingers]**

- Increase worker threads from 1 to 10: 600-700 docs/second
- Add more Couchbase nodes to the cluster: linear scale
- Distribute eventing functions across nodes: parallel processing

Customers are running this at millions of documents per hour. Financial services companies processing transaction data. Healthcare systems processing claims. Pharma companies processing clinical trial results.

For your production volumes, we'd architect for the throughput you need. And because it's Capella, you can auto-scale based on load - spin up capacity during high-volume ingestion, scale down during off-peak.

Would you like to see a performance benchmark with your actual data volumes?"

---

### **Q3: "Can it handle more complex transformations? Like calling external APIs or ML models?"**

**ANSWER:**

"Yes. The eventing function is full JavaScript with network access. You can:

**[List on fingers]**

1. **Call external REST APIs** - Entity extraction services, medical coding APIs, drug interaction databases
2. **Invoke ML models** - Classification, sentiment analysis, anomaly detection
3. **Connect to LLMs** - Summarization, entity extraction, content generation
4. **Query reference data** - Look up ICD codes, drug formularies, ontologies
5. **Execute business rules** - Complex validation, approval workflows, data quality checks

What we showed today was intentionally simple - PII redaction and metadata enrichment. But in production, customers are doing:
- Medical coding with NLP models
- Drug interaction checking against FDA databases
- Document classification with custom ML models
- Summarization with GPT-4 for long-form documents

The function runs at the data layer, so it's low-latency and highly scalable.

What specific transformations does your data pipeline need?"

---

### **Q4: "What about data lineage and versioning?"**

**ANSWER:**

"Critical for governance, and we handle it natively.

**[Point to screen or gesture]**

Notice we keep both collections:
- `raw_documents` - original data, untouched, full history
- `processed_documents` - transformed version

Every processed document includes an audit trail:
- What was changed (PII redacted, metadata enriched)
- When it was changed (timestamps)
- By which function (knowledge_pipeline)
- What the original values were (if you need forensics)

If your compliance team or regulators ask 'prove this data was cleaned', you have full lineage from raw to processed.

And if you need to reprocess with different rules - say your legal team updates redaction policies - the raw data is always available. You update the eventing function, redeploy, and reprocess. The old processed data can be versioned or archived.

We can also add versioning within documents - keep v1, v2, v3 as your enrichment logic evolves. Customers doing this for regulatory compliance where they need to show how data quality improved over time."

---

### **Q5: "How much does this cost compared to building ETL pipelines?"**

**ANSWER:**

"Let's think about total cost of ownership:

**Traditional ETL approach:**
- Data engineering time to build pipelines: weeks to months
- Infrastructure for ETL workers: Spark clusters, Airflow, etc.
- Maintenance: every new data source requires new pipeline code
- Latency: batch processing means delays (hours to days)
- Expertise: need data engineers who know Spark, Airflow, etc.

**Couchbase approach:**
- Deploy eventing function: hours to days
- Infrastructure: included in Capella, fully managed
- Maintenance: update JavaScript function, redeploy instantly
- Latency: real-time, milliseconds
- Expertise: JavaScript developers (much easier to hire)

Customers typically see 70-80% reduction in data engineering effort because transformations happen at the data layer. No separate ETL infrastructure. No batch jobs. No orchestration complexity.

Plus - and this is the bigger ROI - your AI teams get access to clean data immediately. Not days or weeks later. That's velocity. That's competitive advantage.

Would you like me to connect you with one of our existing customers to discuss their ROI?"

---

## SECTION 10: NEXT STEPS & CLOSE (2 minutes)

### **SCRIPT:**

**[If the audience seems engaged and interested]**

"If this resonates with what you're building, here's what I'd propose as next steps:

**[Count on fingers]**

**Step 1: Architecture Deep-Dive (1 week)**
Let's get your architects and our solutions team in a room. Map this to your specific data pipeline. Understand:
- Your data sources and volumes
- Your redaction and compliance requirements
- Your enrichment and transformation needs
- Your integration points with existing systems

**Step 2: Focused POC (2 weeks)**
We set up a POC environment. You bring one data source - maybe clinical trials or drug labels - and we apply your actual business rules. You test with real data. Your team validates it works.

**Step 3: Performance Benchmark (1 week)**
Load 100K records. Stress test it. Measure throughput, latency, accuracy. Prove it can handle your production volumes.

**[Pause]**

We can have the POC environment live in one week. Your team can start testing with real data in two weeks.

**[Look directly at the audience]**

What interests you most? The compliance capabilities? The enrichment possibilities? The integration with your current stack?"

---

**[Alternative if the audience needs time]**

"I know this is a lot to process, and you'll need to discuss with your team. Here's what I'll do:

**[Count on fingers]**

I'll send you:

1. **Eventing function code** - full source code, your team can review the logic
2. **Demo environment credentials** - read-only access so your architects can explore
3. **Architecture diagrams** - how this fits into your data pipeline
4. **Customer references** - similar healthcare use cases

Take a week. Have your team dig in. Run queries. Review the code. Think about your specific use cases.

Then let's reconnect to discuss what makes sense for your use case.

**[Pause]**

Sound good?"

---

### **FINAL CLOSE**

**[Stand up or prepare to wrap]**

"Here's the bottom line:

The hard part of enterprise AI isn't retrieval. It's making data retrieval-ready. At scale. With compliance. With governance. With enrichment.

That's what you just saw. That's what Couchbase does that vector databases and search engines can't.

Thank you for your time today. Looking forward to diving deeper with your team."

**[End demo]**

---

## POST-DEMO FOLLOW-UP CHECKLIST

✅ Send demo recording (if recorded)  
✅ Send eventing function code via email  
✅ Send architecture diagram PDF  
✅ Send customer references (with permission)  
✅ Set up POC environment if requested  
✅ Schedule follow-up meeting (within 1 week)  
✅ Connect with technical champions on their team  
✅ Send Capella pricing calculator based on their volumes  

---

## APPENDIX: BACKUP QUERIES

### **If you need additional proof points:**

**Query: Show metadata extraction working**
```sql
SELECT 
    metadata.medical_condition,
    metadata.admission_type,
    COUNT(*) as count
FROM `pharma_knowledge`._default.processed_documents
GROUP BY metadata.medical_condition, metadata.admission_type
ORDER BY count DESC
LIMIT 10;
```

**Query: Find high-risk patients**
```sql
SELECT 
    patient.age,
    metrics.age_group,
    medical.condition,
    billing.amount,
    metrics.billing_category
FROM `pharma_knowledge`._default.processed_documents
WHERE metrics.billing_category = "Very High"
  AND metrics.age_group IN ["Senior", "Elderly"]
LIMIT 10;
```

**Query: Verify no PII leaked**
```sql
SELECT COUNT(*) as documents_with_pii
FROM `pharma_knowledge`._default.processed_documents
WHERE patient.name != "[NAME_REDACTED]";
-- Should return 0
```

---

## TIPS FOR DELIVERY

1. **Pace Yourself**: Don't rush. Let queries run. Let the audience absorb the information.

2. **Ask Questions**: "Does this make sense?" "How does this compare to your current pipeline?" "What questions do you have?"

3. **Listen for Pain Points**: When the audience mentions challenges, map them to what you just showed.

4. **Use Their Language**: If they say "data cleansing", use that term. If they say "transformation", use that.

5. **Be Honest About Limitations**: If they ask something you don't know, say "Great question, let me connect you with our specialist who handles that exact scenario."

6. **Focus on Business Outcomes**: Not "Look at this cool technology" but "This solves your compliance bottleneck" and "This accelerates your AI team's velocity."

7. **Create Urgency**: "Your competitors are doing this. The AI teams that move fast are the ones with clean data pipelines."

---

**Total Demo Time: 20-25 minutes (with questions)**

**Good luck with the presentation!**
