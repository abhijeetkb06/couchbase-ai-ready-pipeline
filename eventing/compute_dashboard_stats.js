/**
 * Eventing Function: ComputeDashboardStats
 *
 * Purpose: Keeps dashboard statistics in sync with processed_documents.
 *          Uses a 5-second debounce timer so bulk mutations trigger only
 *          one recompute instead of thousands.
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
 */

function OnUpdate(doc, meta) {
    if (doc.type !== "processed_patient_record") {
        return;
    }
    var fireAt = new Date();
    fireAt.setSeconds(fireAt.getSeconds() + 5);
    createTimer(doRecompute, fireAt, "dashboard_stats_recompute", {});
}

function OnDelete(meta, options) {
    var fireAt = new Date();
    fireAt.setSeconds(fireAt.getSeconds() + 5);
    createTimer(doRecompute, fireAt, "dashboard_stats_recompute", {});
}

function doRecompute(context) {
    log("Recomputing dashboard stats...");

    var stats = {
        type: "dashboard_stats",
        total_patients: 0,
        with_embeddings: 0,
        unique_conditions: 0,
        unique_medications: 0,
        by_age_group: {},
        by_billing: {},
        by_condition: {},
        by_medication: {},
        last_updated: new Date().toISOString()
    };

    // Totals
    var r1 = N1QL(
        "SELECT COUNT(*) AS total, " +
        "COUNT(CASE WHEN vector IS NOT MISSING THEN 1 END) AS with_embeddings, " +
        "COUNT(DISTINCT medical.`condition`) AS unique_conditions, " +
        "COUNT(DISTINCT medical.medication) AS unique_medications " +
        "FROM `pharma_knowledge`.`_default`.`processed_documents` " +
        "WHERE type = \"processed_patient_record\"",
        [],
        { 'consistency': 'request' }
    );
    for (var row of r1) {
        stats.total_patients = row.total;
        stats.with_embeddings = row.with_embeddings;
        stats.unique_conditions = row.unique_conditions;
        stats.unique_medications = row.unique_medications;
    }
    r1.close();

    // By age group
    var r2 = N1QL(
        "SELECT metrics.age_group AS cat, COUNT(*) AS cnt " +
        "FROM `pharma_knowledge`.`_default`.`processed_documents` " +
        "WHERE type = \"processed_patient_record\" AND metrics.age_group IS NOT MISSING " +
        "GROUP BY metrics.age_group",
        [],
        { 'consistency': 'request' }
    );
    for (var row of r2) {
        stats.by_age_group[row.cat] = row.cnt;
    }
    r2.close();

    // By billing category
    var r3 = N1QL(
        "SELECT metrics.billing_category AS cat, COUNT(*) AS cnt " +
        "FROM `pharma_knowledge`.`_default`.`processed_documents` " +
        "WHERE type = \"processed_patient_record\" AND metrics.billing_category IS NOT MISSING " +
        "GROUP BY metrics.billing_category",
        [],
        { 'consistency': 'request' }
    );
    for (var row of r3) {
        stats.by_billing[row.cat] = row.cnt;
    }
    r3.close();

    // By medical condition
    var r4 = N1QL(
        "SELECT medical.`condition` AS cat, COUNT(*) AS cnt " +
        "FROM `pharma_knowledge`.`_default`.`processed_documents` " +
        "WHERE type = \"processed_patient_record\" AND medical.`condition` IS NOT MISSING " +
        "GROUP BY medical.`condition`",
        [],
        { 'consistency': 'request' }
    );
    for (var row of r4) {
        stats.by_condition[row.cat] = row.cnt;
    }
    r4.close();

    // By medication
    var r5 = N1QL(
        "SELECT medical.medication AS cat, COUNT(*) AS cnt " +
        "FROM `pharma_knowledge`.`_default`.`processed_documents` " +
        "WHERE type = \"processed_patient_record\" " +
        "AND medical.medication IS NOT MISSING " +
        "AND medical.medication != \"None\" " +
        "GROUP BY medical.medication",
        [],
        { 'consistency': 'request' }
    );
    for (var row of r5) {
        stats.by_medication[row.cat] = row.cnt;
    }
    r5.close();

    // Write to stats collection
    stats_col["dashboard_stats"] = stats;

    log("Dashboard stats updated: " + stats.total_patients + " patients, " +
        stats.with_embeddings + " with embeddings");
}
