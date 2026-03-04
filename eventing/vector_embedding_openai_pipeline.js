function OnUpdate(doc, meta, xattrs) {
    log("[1] OnUpdate CALLED for: " + meta.id);
    
    if (doc.vector) {
        log("[2] SKIP - already has vector: " + meta.id);
        return;
    }
    
    if (doc.type !== "processed_patient_record") {
        log("[3] SKIP - wrong type: " + doc.type + " for: " + meta.id);
        return;
    }
    
    log("[4] Processing document: " + meta.id);

    try {
        var parts = [];
        var medical = doc.medical || {};
        var patient = doc.patient || {};
        var metrics = doc.metrics || {};
        
        log("[5] Building summary - condition: " + medical.condition);
        
        if (metrics.age_group) parts.push(metrics.age_group + " patient");
        if (patient.gender) parts.push(patient.gender.toLowerCase());
        if (medical.condition) parts.push("diagnosed with " + medical.condition);
        if (medical.admission_type) parts.push(medical.admission_type.toLowerCase() + " admission");
        if (medical.medication && medical.medication !== "None") parts.push("prescribed " + medical.medication);
        if (medical.test_results) parts.push("test results " + medical.test_results.toLowerCase());
        if (medical.hospital) parts.push("at " + medical.hospital);
        if (metrics.billing_category) parts.push(metrics.billing_category.toLowerCase() + " cost case");
        
        var textToEmbed = parts.join(", ");
        log("[6] Text to embed: " + textToEmbed);
        
        if (!textToEmbed || textToEmbed.length < 10) {
            log("[7] SKIP - text too short");
            return;
        }
        
        // Build request object like the working example
        var request = {
            body: {
                input: textToEmbed,
                model: "text-embedding-3-small"
            }
        };
        
        log("[8] Calling OpenAI API...");

        var response = curl("POST", openaiApi, request);

        log("[9] API response status: " + response.status);

        if (response.status === 200) {
            // response.body is already a parsed JSON object - NO JSON.parse() needed
            var response_body = response.body;
            
            log("[10] Response received");
            
            if (response_body.data && response_body.data[0] && response_body.data[0].embedding) {
                var embedding = response_body.data[0].embedding;
                log("[11] Embedding length: " + embedding.length);
                
                doc.vector = embedding;
                doc.medical_summary = textToEmbed;
                dst_bucket[meta.id] = doc;
                log("[12] SUCCESS: " + meta.id + " with " + embedding.length + " dims");
            } else {
                log("[13] No embedding in response");
            }
        } else {
            log("[14] ERROR - status: " + response.status + " body: " + JSON.stringify(response.body));
        }

    } catch (e) {
        log("[99] EXCEPTION: " + e);
    }
}

function OnDelete(meta, options) {
}
