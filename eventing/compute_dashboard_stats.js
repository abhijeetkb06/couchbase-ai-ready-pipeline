/**
 * Eventing Function: ComputeDashboardStats
 *
 * Recomputes dashboard stats via N1QL aggregates on every mutation.
 * No timers - just accurate recompute each time.
 *
 * Source: pharma_knowledge._default.processed_documents
 * Metadata: pharma_knowledge.storage.metadata
 * Bucket Binding: stats_col (read-write) -> pharma_knowledge._default.stats
 */

function OnUpdate(doc, meta) {
    if (doc.type !== "processed_patient_record") {
        return;
    }

    var doctype = "processed_patient_record";
    var none_val = "None";

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

    // Total patients
    var r1 =
        SELECT COUNT(*) AS total
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype;
    for (var item of r1) {
        stats.total_patients = item.total;
    }
    r1.close();

    // With embeddings
    var r2 =
        SELECT COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype AND vector IS NOT MISSING;
    for (var item of r2) {
        stats.with_embeddings = item.cnt;
    }
    r2.close();

    // Unique conditions
    var r3 =
        SELECT COUNT(DISTINCT medical.condition) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype;
    for (var item of r3) {
        stats.unique_conditions = item.cnt;
    }
    r3.close();

    // Unique medications
    var r4 =
        SELECT COUNT(DISTINCT medical.medication) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype
        AND medical.medication IS NOT MISSING
        AND medical.medication != $none_val;
    for (var item of r4) {
        stats.unique_medications = item.cnt;
    }
    r4.close();

    // By age group
    var r5 =
        SELECT metrics.age_group AS cat, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype AND metrics.age_group IS NOT MISSING
        GROUP BY metrics.age_group;
    for (var item of r5) {
        stats.by_age_group[item.cat] = item.cnt;
    }
    r5.close();

    // By billing category
    var r6 =
        SELECT metrics.billing_category AS cat, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype AND metrics.billing_category IS NOT MISSING
        GROUP BY metrics.billing_category;
    for (var item of r6) {
        stats.by_billing[item.cat] = item.cnt;
    }
    r6.close();

    // By medical condition
    var r7 =
        SELECT medical.condition AS cat, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype AND medical.condition IS NOT MISSING
        GROUP BY medical.condition;
    for (var item of r7) {
        stats.by_condition[item.cat] = item.cnt;
    }
    r7.close();

    // By medication
    var r8 =
        SELECT medical.medication AS cat, COUNT(*) AS cnt
        FROM `pharma_knowledge`.`_default`.`processed_documents`
        WHERE type = $doctype
        AND medical.medication IS NOT MISSING
        AND medical.medication != $none_val
        GROUP BY medical.medication;
    for (var item of r8) {
        stats.by_medication[item.cat] = item.cnt;
    }
    r8.close();

    stats_col["dashboard_stats"] = stats;
    log("Dashboard stats updated: " + stats.total_patients + " patients, " +
        stats.with_embeddings + " with embeddings");
}

function OnDelete(meta, options) {
    log("Document deleted: " + meta.id);
}
