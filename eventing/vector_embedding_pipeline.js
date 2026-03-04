/**
 * Eventing Function: Vector Embedding Pipeline
 * 
 * Purpose: Enriches processed patient records with vector embeddings
 *          using HuggingFace BGE model for semantic search
 * 
 * Trigger: Documents in processed_documents collection
 * Output:  Updates SAME document with embedding (no data duplication!)
 * 
 * Actions:
 * 1. Build medical_summary text from patient data
 * 2. Call HuggingFace Inference API to generate 768-dim embedding
 * 3. Update the SAME document with embedding vector
 * 
 * Architecture:
 *   raw_documents  -->  processed_documents (with PII redacted + metadata enriched + embeddings)
 *                       ^
 *                       |__ This function adds embeddings to existing processed docs
 * 
 * Configuration Required:
 * - URL Binding: hfApi -> https://router.huggingface.co/hf-inference/models/BAAI/bge-base-en-v1.5/pipeline/feature-extraction
 *   - Auth Type: Bearer
 *   - Bearer Key: <your-huggingface-api-token>
 * - Bucket Binding: src_bucket (read-write) -> pharma_knowledge._default.processed_documents
 *   NOTE: Points to SAME collection - updates documents in place, no duplication!
 */

function OnUpdate(doc, meta) {
    // Skip if already has embedding or not a processed patient record
    if (doc.embedding || doc.type !== "processed_patient_record") {
        return;
    }
    
    log("Generating embedding for: " + meta.id);
    
    try {
        // ========================================
        // STEP 1: BUILD MEDICAL SUMMARY TEXT
        // ========================================
        var medical = doc.medical || {};
        var patient = doc.patient || {};
        var metrics = doc.metrics || {};
        
        // Create rich text for semantic understanding
        var medical_summary = buildMedicalSummary(patient, medical, metrics);
        
        if (!medical_summary || medical_summary.length < 10) {
            log("Insufficient data for embedding: " + meta.id);
            return;
        }
        
        log("Medical summary: " + medical_summary);
        
        // ========================================
        // STEP 2: CALL HUGGINGFACE API
        // ========================================
        var response = curl("POST", hfApi, {
            body: JSON.stringify({ inputs: medical_summary }),
            headers: { "Content-Type": "application/json" }
        });
        
        log("HuggingFace API status: " + response.status);
        
        if (response.status !== 200) {
            log("HuggingFace API error for " + meta.id + ": " + response.body);
            doc.embedding_status = "failed";
            doc.embedding_error = String(response.body);
            src_bucket[meta.id] = doc;
            return;
        }
        
        // ========================================
        // STEP 3: PARSE EMBEDDING RESPONSE
        // ========================================
        var embedding = parseEmbeddingResponse(response.body);
        
        if (!embedding || embedding.length === 0) {
            log("Failed to parse embedding for: " + meta.id);
            doc.embedding_status = "failed";
            doc.embedding_error = "Parse error";
            src_bucket[meta.id] = doc;
            return;
        }
        
        // ========================================
        // STEP 4: UPDATE DOCUMENT WITH EMBEDDING
        // ========================================
        doc.embedding = embedding;
        doc.medical_summary = medical_summary;
        doc.embedding_status = "success";
        doc.embedding_generated_at = new Date().toISOString();
        doc.embedding_model = "BAAI/bge-base-en-v1.5";
        doc.embedding_dimensions = embedding.length;
        
        src_bucket[meta.id] = doc;
        
        log("Embedding generated for " + meta.id + " - " + embedding.length + " dimensions");
        
    } catch (err) {
        log("Error generating embedding for " + meta.id + ": " + err.toString());
        doc.embedding_status = "failed";
        doc.embedding_error = err.toString();
        src_bucket[meta.id] = doc;
    }
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function buildMedicalSummary(patient, medical, metrics) {
    // Build a rich text description for semantic embedding
    var parts = [];
    
    // Patient demographics (age group, not exact age for privacy)
    if (metrics.age_group) {
        parts.push(metrics.age_group + " patient");
    }
    
    if (patient.gender) {
        parts.push(patient.gender.toLowerCase());
    }
    
    // Medical condition - most important for semantic search
    if (medical.condition) {
        parts.push("diagnosed with " + medical.condition);
    }
    
    // Admission context
    if (medical.admission_type) {
        parts.push(medical.admission_type.toLowerCase() + " admission");
    }
    
    // Treatment info
    if (medical.medication && medical.medication !== "None") {
        parts.push("prescribed " + medical.medication);
    }
    
    // Test results
    if (medical.test_results) {
        parts.push("test results " + medical.test_results.toLowerCase());
    }
    
    // Hospital context
    if (medical.hospital) {
        parts.push("at " + medical.hospital);
    }
    
    // Billing category for similar case finding
    if (metrics.billing_category) {
        parts.push(metrics.billing_category.toLowerCase() + " cost case");
    }
    
    return parts.join(", ");
}

function parseEmbeddingResponse(responseBody) {
    var respBody = String(responseBody).trim();
    var embedding = null;
    
    try {
        var parsed = JSON.parse(respBody);
        
        // HuggingFace returns [[vector]] for single input
        if (Array.isArray(parsed) && Array.isArray(parsed[0])) {
            embedding = parsed[0];
        } else if (Array.isArray(parsed)) {
            embedding = parsed;
        }
    } catch (e) {
        log("JSON parse failed, trying fallback: " + e.toString());
        
        // Fallback: try CSV split
        embedding = respBody.split(",").map(function(v) {
            return parseFloat(v);
        });
    }
    
    return embedding;
}

function OnDelete(meta, options) {
    log("Document deleted: " + meta.id);
}
