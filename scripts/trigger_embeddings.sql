-- Vector Embedding Trigger Queries
-- Run these in Capella Query Workbench after deploying the eventing function

-- 1. Trigger a small batch first to test (10 documents)
UPDATE pharma_knowledge._default.processed_documents
SET _trigger = NOW_MILLIS()
WHERE type = "processed_patient_record" AND vector IS MISSING
LIMIT 10;

-- 2. Check if embeddings are being generated
SELECT 
    COUNT(*) FILTER (WHERE vector IS NOT MISSING) AS with_vector,
    COUNT(*) FILTER (WHERE vector IS MISSING AND type = "processed_patient_record") AS without_vector
FROM pharma_knowledge._default.processed_documents;

-- 3. View sample documents with embeddings
SELECT META().id, medical_summary, ARRAY_LENGTH(vector) AS vector_dims
FROM pharma_knowledge._default.processed_documents
WHERE vector IS NOT MISSING
LIMIT 5;

-- 4. Trigger larger batch (100 documents)
UPDATE pharma_knowledge._default.processed_documents
SET _trigger = NOW_MILLIS()
WHERE type = "processed_patient_record" AND vector IS MISSING
LIMIT 100;

-- 5. Trigger all remaining documents (run multiple times if needed)
UPDATE pharma_knowledge._default.processed_documents
SET _trigger = NOW_MILLIS()
WHERE type = "processed_patient_record" AND vector IS MISSING
LIMIT 1000;
