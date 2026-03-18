2️⃣ Duplicate Primary Key Check (VERY IMPORTANT)
SELECT entity, pk_column, pk_value, COUNT(*) AS cnt
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
GROUP BY entity, pk_column, pk_value
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
🧠 Observation:

Expected duplicates (daily rejects)

Identify high-frequency failing PKs

3️⃣ Invalid PK Format Check
SELECT *
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE SAFE_CAST(pk_value AS INT64) IS NULL;
🧠 Observation:

Non-numeric / corrupted PKs

4️⃣ Reject Reason Analysis (MOST IMPORTANT)
SELECT reject_reason, COUNT(*) AS cnt
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
GROUP BY reject_reason
ORDER BY cnt DESC;
🧠 From your screenshot:

"mandatory column cannot be empty" → major issue

Missing fields like:

UNT_KEY_POLICY_NO

UNT_KEY_CONTR_CD

👉 This is data completeness issue

5️⃣ Entity-wise Failure Analysis
SELECT entity, COUNT(*) AS reject_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
GROUP BY entity
ORDER BY reject_count DESC;
6️⃣ Unprocessed PK Check (Your Lead's Requirement ⭐)
SELECT r.pk_value
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg` r
LEFT JOIN `TARGET_TABLE` t
ON r.pk_value = t.pk_value
WHERE t.pk_value IS NULL;

👉 This gives:

PKs not loaded into main table

These are pending / failed records

7️⃣ NULL Reject Reason Check
SELECT COUNT(*) 
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE reject_reason IS NULL;
