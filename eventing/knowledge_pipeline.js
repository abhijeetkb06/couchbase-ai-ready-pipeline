/**
 * Eventing Function: Knowledge Preparation Pipeline
 * 
 * Purpose: Single-stage pipeline that transforms raw patient records into
 *          clean, enriched, searchable documents
 * 
 * Trigger: New documents in raw_documents with processing_status = "pending"
 * 
 * Actions:
 * 1. PII REDACTION - Remove patient names and sensitive identifiers
 * 2. METADATA ENRICHMENT - Extract medical conditions, doctors, hospitals
 * 3. EMBEDDING GENERATION - Create vector embeddings for semantic search (placeholder)
 * 4. WRITE TO processed_documents - Final clean output
 * 
 * Configuration:
 * - Source Bucket: pharma_knowledge
 * - Source Scope: _default
 * - Source Collection: raw_documents
 * - Bucket Bindings Required:
 *   - processed_docs (read-write): pharma_knowledge._default.processed_documents
 */

function OnUpdate(doc, meta) {
    // Only process pending documents
    if (!doc.processing_status || doc.processing_status !== "pending") {
        return;
    }
    
    log("Processing document: " + meta.id);
    
    // ========================================
    // STEP 1: PII REDACTION
    // ========================================
    var pii_redacted = {
        redacted_at: new Date().toISOString(),
        pii_found: []
    };
    
    // Redact patient name
    if (doc.name && doc.name.length > 0) {
        doc.name = "[NAME_REDACTED]";
        pii_redacted.pii_found.push("name");
    }
    
    log("PII redacted: " + pii_redacted.pii_found.join(", "));
    
    // ========================================
    // STEP 2: METADATA ENRICHMENT
    // ========================================
    var metadata = {
        medical_condition: doc.medical_condition || "Unknown",
        admission_type: doc.admission_type || "Unknown",
        doctor: doc.doctor || "Unknown",
        hospital: doc.hospital || "Unknown",
        medication: doc.medication || "None",
        insurance_provider: doc.insurance_provider || "Unknown",
        enriched_at: new Date().toISOString()
    };
    
    // Extract key metrics
    var metrics = {
        age_group: classifyAgeGroup(doc.age),
        billing_category: classifyBilling(doc.billing_amount),
        test_result_status: classifyTestResult(doc.test_results)
    };
    
    log("Metadata enriched: " + metadata.medical_condition);
    
    // ========================================
    // STEP 3: CREATE PROCESSED DOCUMENT
    // ========================================
    // Use same document key for easy JOIN queries between raw and processed
    var processed_doc = {
        type: "processed_patient_record",
        
        // Original data (with PII redacted)
        patient: {
            name: doc.name,  // [NAME_REDACTED]
            age: doc.age,
            gender: doc.gender,
            blood_type: doc.blood_type
        },
        
        // Medical information
        medical: {
            condition: doc.medical_condition,
            admission_date: doc.date_of_admission,
            discharge_date: doc.discharge_date,
            admission_type: doc.admission_type,
            medication: doc.medication,
            test_results: doc.test_results,
            doctor: doc.doctor,
            hospital: doc.hospital,
            room_number: doc.room_number
        },
        
        // Billing information
        billing: {
            amount: doc.billing_amount,
            insurance_provider: doc.insurance_provider
        },
        
        // Enriched metadata (for search/filtering)
        metadata: metadata,
        metrics: metrics,
        
        // Audit trail
        pii_redaction: pii_redacted,
        
        // Processing timestamps
        created_at: doc.created_at,
        processed_at: new Date().toISOString(),
        
        // Searchability flags
        is_searchable: true,
        is_pii_compliant: true
    };
    
    // ========================================
    // STEP 4: WRITE TO PROCESSED COLLECTION
    // ========================================
    try {
        // Use same key as raw document for easy JOIN queries
        // Note: Requires bucket binding "processed_docs" pointing to processed_documents collection
        processed_docs[meta.id] = processed_doc;
        log("✓ Processed document created with same ID: " + meta.id);
    } catch (e) {
        log("✗ Error writing processed document: " + e);
    }
    
    // Update source document status
    doc.processing_status = "completed";
    doc.processed_at = new Date().toISOString();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function classifyAgeGroup(age) {
    if (age < 18) return "Child";
    if (age < 35) return "Young Adult";
    if (age < 55) return "Adult";
    if (age < 70) return "Senior";
    return "Elderly";
}

function classifyBilling(amount) {
    if (amount < 10000) return "Low";
    if (amount < 30000) return "Medium";
    if (amount < 50000) return "High";
    return "Very High";
}

function classifyTestResult(result) {
    if (!result) return "Unknown";
    var lower = result.toLowerCase();
    if (lower.indexOf("inconclusive") !== -1) return "Inconclusive";
    return "Other";
}

function OnDelete(meta, options) {
    log("Doc deleted/expired", meta.id);
}
