/**
 * Eventing Function: ComputeDashboardStats
 *
 * Purpose: Keeps dashboard statistics in sync with processed_documents.
 *          Uses a 5-second debounce timer so bulk mutations trigger only
 *          one recompute instead of thousands.
 *
 * Trigger: Any mutation in processed_documents collection
 *
 * How it works:
 *   1. OnUpdate/OnDelete fires on every processed_documents mutation
 *   2. A timer with a FIXED reference is created (5 seconds from now)
 *      - Same reference = previous pending timer is overwritten = debounce
 *   3. When the timer fires, N1QL aggregate queries compute fresh stats
 *   4. Result is written to stats collection as "dashboard_stats" document
 *
 * Configuration:
 *   Source Bucket:     pharma_knowledge
 *   Source Scope:      _default
 *   Source Collection: processed_documents
 *   Metadata Bucket:   pharma_knowledge
 *   Metadata Scope:    storage
 *   Metadata Collection: metadata
 *
 * Bucket Bindings:
 *   stats_col (read-write) -> pharma_knowledge._default.stats
 *
 * The dashboard_stats document schema matches what intelligent_search.py expects:
 *   {
 *     total_patients, with_embeddings, unique_conditions, unique_medications,
 *     by_age_group: {}, by_billing: {}, by_condition: {}, by_medication: {},
 *     computed_at
 *   }
 */

function OnUpdate(doc, meta) {
    // Only react to processed patient records
    if (doc.type !== "processed_patient_record") {
        return;
    }
    scheduleRecompute();
}

function OnDelete(meta, options) {
    scheduleRecompute();
}

function scheduleRecompute() {
    var fireAt = new Date();
    fireAt.setSeconds(fireAt.getSeconds() + 5);
    // Fixed reference = overwrites any pending timer = debounce
    createTimer(recomputeStats, fireAt, "dashboard_stats_recompute", {});
}

function recomputeStats(context) {
    log("Recomputing dashboard stats...");

    var stats = {
        total_patients: 0,
        with_embeddings: 0,
        unique_conditions: 0,
        unique_medications: 0,
        by_age_group: {},
        by_billing: {},
        by_condition: {},
        by_medication: {},
        computed_at: new Date().toISOString()
    };

    // ========================================
    // Totals
    // ========================================
    for (var row of SELECT COUNT(*) AS total,
            COUNT(CASE WHEN vector IS NOT MISSING THEN 1 END) AS with_embeddings,
            COUNT(DISTINCT medical.`condition`) AS unique_conditions,
            COUNT(DISTINCT medical.medication) AS unique_medications
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = "processed_patient_record") {
        stats.total_patients = row.total;
        stats.with_embeddings = row.with_embeddings;
        stats.unique_conditions = row.unique_conditions;
        stats.unique_medications = row.unique_medications;
    }

    // ========================================
    // Breakdown: By Age Group
    // ========================================
    for (var row of SELECT metrics.age_group AS category, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = "processed_patient_record" AND metrics.age_group IS NOT MISSING
        GROUP BY metrics.age_group) {
        stats.by_age_group[row.category] = row.cnt;
    }

    // ========================================
    // Breakdown: By Billing Category
    // ========================================
    for (var row of SELECT metrics.billing_category AS category, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = "processed_patient_record" AND metrics.billing_category IS NOT MISSING
        GROUP BY metrics.billing_category) {
        stats.by_billing[row.category] = row.cnt;
    }

    // ========================================
    // Breakdown: By Medical Condition
    // ========================================
    for (var row of SELECT medical.`condition` AS category, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = "processed_patient_record" AND medical.`condition` IS NOT MISSING
        GROUP BY medical.`condition`) {
        stats.by_condition[row.category] = row.cnt;
    }

    // ========================================
    // Breakdown: By Medication
    // ========================================
    for (var row of SELECT medical.medication AS category, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = "processed_patient_record"
        AND medical.medication IS NOT MISSING
        AND medical.medication != "None"
        GROUP BY medical.medication) {
        stats.by_medication[row.category] = row.cnt;
    }

    // ========================================
    // Write to stats collection
    // ========================================
    stats_col["dashboard_stats"] = stats;

    log("Dashboard stats updated: " +
        stats.total_patients + " patients, " +
        stats.with_embeddings + " with embeddings, " +
        stats.unique_conditions + " conditions, " +
        stats.unique_medications + " medications");
}
