🔹 1. Basic Data Understanding

Run this first:

SELECT COUNT(*) FROM `project.dataset.ta_reject_extract_stg`;

👉 You already have ~1B+ records → so don’t scan full table blindly

🔹 2. Check Reject Reason Distribution (MOST IMPORTANT)
SELECT 
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
GROUP BY reject_reason
ORDER BY cnt DESC;

🎯 This tells:

Top failure reasons

Where most issues are coming from

🔹 3. Entity-wise Analysis
SELECT 
  entity,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
GROUP BY entity
ORDER BY reject_count DESC;

👉 Helps answer:

Which table/entity has most issues

🔹 4. Missing Mandatory Columns Analysis

From your screenshot:
👉 "mandatory column cannot empty"

Drill down:

SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE reject_reason LIKE '%mandatory%'
GROUP BY entity, reject_reason
ORDER BY cnt DESC;
🔹 5. Null / Empty Text Analysis

Your lead specifically mentioned this ⚠️

SELECT COUNT(*) 
FROM `project.dataset.ta_reject_extract_stg`
WHERE text IS NULL;

Also:

SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE text IS NULL
LIMIT 100;

👉 You need to analyze:

Why text is NULL only for some files

🔹 6. Primary Key Issues (CRITICAL)
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE pk_value IS NULL
   OR SAFE_CAST(pk_value AS INT64) IS NULL;

👉 Matches what your lead said:

“safe casting… if string → null”

🔹 7. Duplicate PK Check
SELECT 
  pk_value,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
GROUP BY pk_value
HAVING cnt > 1
ORDER BY cnt DESC;
🔹 8. File-wise Analysis
SELECT 
  file_name,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
GROUP BY file_name
ORDER BY reject_count DESC;

👉 Helps:

Identify problematic files

🔹 9. Time-based Analysis
SELECT 
  DATE(extracted_ts) AS dt,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
GROUP BY dt
ORDER BY dt DESC;

👉 Check:

Any spike in failures

🔹 10. Compare with Source (VERY IMPORTANT 🔥)

👉 Your lead emphasized this:

You need to check:

Records expected vs received vs rejected

Example:

-- Expected records (source)
SELECT COUNT(*) FROM source_table;

-- Loaded records
SELECT COUNT(*) FROM target_table;

-- Rejected records
SELECT COUNT(*) FROM ta_reject_extract_stg;

👉 Then validate:

Expected = Loaded + Rejected ?
🔹 11. Sample Deep Dive (Manual Analysis)

Pick few rows:

SELECT *
FROM `project.dataset.ta_reject_extract_stg`
LIMIT 100;
=============

🚀 🔥 0. Always Use Filter (VERY IMPORTANT for 1B records)

👉 Don’t scan full table — use this everywhere:

WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1

(or use specific date if needed)

📊 1. Overall Summary
SELECT 
  COUNT(*) AS total_rejects,
  COUNT(DISTINCT entity) AS total_entities,
  COUNT(DISTINCT file_name) AS total_files
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1;
📊 2. Reject Reason Distribution (TOP PRIORITY)
SELECT 
  reject_reason,
  COUNT(*) AS reject_count,
  ROUND(COUNT(*) * 100 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY reject_reason
ORDER BY reject_count DESC;

👉 Use this in PPT → “Top Failure Reasons”

📊 3. Entity-wise Reject Analysis
SELECT 
  entity,
  COUNT(*) AS reject_count,
  ROUND(COUNT(*) * 100 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity
ORDER BY reject_count DESC;
📊 4. Entity + Reject Reason (Granular View 🔥)
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, reject_reason
ORDER BY cnt DESC;

👉 This is most important for root cause

📊 5. Mandatory Column Issues (From your screenshot)
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND reject_reason LIKE '%mandatory%'
GROUP BY entity, reject_reason
ORDER BY cnt DESC;
📊 6. Null / Empty TEXT Analysis ⚠️
-- Count
SELECT 
  COUNT(*) AS null_text_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NULL;
-- Sample rows
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NULL
LIMIT 100;
📊 7. Primary Key Issues (CRITICAL 🔥)
Invalid PK (string / bad values)
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND SAFE_CAST(pk_value AS INT64) IS NULL;
Null PK
SELECT COUNT(*) 
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND pk_value IS NULL;
📊 8. Duplicate Primary Key Analysis
SELECT 
  pk_value,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY pk_value
HAVING cnt > 1
ORDER BY cnt DESC;
📊 9. File-wise Reject Analysis 🔥
SELECT 
  file_name,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name
ORDER BY reject_count DESC;
Top Problem Files
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE file_name IN (
  SELECT file_name
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  GROUP BY file_name
  ORDER BY COUNT(*) DESC
  LIMIT 5
)
LIMIT 100;
📊 10. File Size vs Reject Count (Advanced 🔥)
SELECT 
  file_name,
  file_size,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name, file_size
ORDER BY reject_count DESC;

👉 Helps identify:

Large files → more failures?

📊 11. Time-based Analysis (Trend)
SELECT 
  TIMESTAMP_TRUNC(extracted_ts, HOUR) AS hour,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY hour
ORDER BY hour;
📊 12. Run ID Analysis
SELECT 
  run_id,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY run_id
ORDER BY reject_count DESC;

👉 Identify:

Which run caused issue

📊 13. Missing Records Validation (IMPORTANT 🔥)

👉 Compare source vs target vs reject

-- Replace table names accordingly

SELECT 
  'SOURCE' AS type, COUNT(*) FROM source_table
UNION ALL
SELECT 
  'TARGET', COUNT(*) FROM target_table
UNION ALL
SELECT 
  'REJECT', COUNT(*) 
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1;

👉 Validation:

SOURCE = TARGET + REJECT ?
📊 14. Reject Reason + File Mapping
SELECT 
  file_name,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name, reject_reason
ORDER BY cnt DESC;
📊 15. Extract Fields from TEXT (VERY ADVANCED 🔥🔥)

Since your text has JSON:

SELECT 
  JSON_EXTRACT_SCALAR(text, '$.UNT_ID') AS unt_id,
  JSON_EXTRACT_SCALAR(text, '$.UNT_KEY_POLICY_NO') AS policy_no,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
LIMIT 100;

👉 Helps:

Validate missing fields inside JSON

📊 16. Mandatory Fields Missing Check (From JSON)
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND (
    JSON_EXTRACT_SCALAR(text, '$.UNT_ID') IS NULL
    OR JSON_EXTRACT_SCALAR(text, '$.UNT_KEY_POLICY_NO') IS NULL
  )
LIMIT 100;
📊 17. Top 10 Problematic Patterns
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, reject_reason
ORDER BY cnt DESC
LIMIT 10;
📄 📊 What You Should Deliver (VERY IMPORTANT)
Excel Sheet Columns:
Entity	File	Reject Reason	Count	%	Issue Type	Root Cause	Fix
🧠 Final Strategy (What your lead expects)

✔ High-level summary
✔ Root cause analysis
✔ Data-level validation
✔ File-level insights
✔ PK + NULL issues
✔ Documentation

🚀 If you want next level (recommended)

I can create for you:

📊 Final PPT (ready to present)

📄 Excel template filled with sample insights

📈 Dashboard queries (Looker / Data Studio)

Just tell: “prepare PPT” 👍

yes you provide me all the details ...also anomolies aswell check the conversation of our previous chats

Yes — based on your earlier discussions, your lead is not asking only for simple counts. They want a full reject-record analysis pack with:

volume analysis

reject reason analysis

entity-wise analysis

file-wise analysis

run-wise analysis

PK issues

null / malformed text issues

source vs target vs reject reconciliation

anomaly checks

trend / spike checks

documentation points for Excel or PPT

Below is a detailed query set you can use directly in BigQuery.

1) First set your working date

Use one date filter everywhere, otherwise this table is too large.

-- Replace this with required date if needed
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

If you do not want DECLARE, then replace all v_dt with a date like:

DATE '2026-03-09'
2) Base filtered dataset

Use this as the base CTE for almost all analysis.

WITH base AS (
  SELECT
    entity,
    pk_column,
    pk_value,
    file_name,
    file_size,
    extracted_ts,
    run_id,
    text,
    reject_reason
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT COUNT(*) AS total_rows
FROM base;
3) Overall summary

This gives your lead the first summary slide.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  COUNT(*) AS total_reject_records,
  COUNT(DISTINCT entity) AS total_entities,
  COUNT(DISTINCT file_name) AS total_files,
  COUNT(DISTINCT run_id) AS total_runs,
  COUNT(DISTINCT pk_column) AS total_pk_columns
FROM base;
4) Reject reason distribution

This is one of the most important queries.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  reject_reason,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM base
GROUP BY reject_reason
ORDER BY reject_count DESC;
5) Entity-wise reject count
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  entity,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM base
GROUP BY entity
ORDER BY reject_count DESC;
6) Entity + reject reason matrix

This is useful for root cause by entity.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  entity,
  reject_reason,
  COUNT(*) AS reject_count
FROM base
GROUP BY entity, reject_reason
ORDER BY reject_count DESC;
7) File-wise reject count

Your lead will likely ask which files are causing the most issues.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  file_name,
  COUNT(*) AS reject_count,
  MIN(file_size) AS file_size
FROM base
GROUP BY file_name
ORDER BY reject_count DESC;
8) File + reject reason analysis
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  file_name,
  reject_reason,
  COUNT(*) AS reject_count
FROM base
GROUP BY file_name, reject_reason
ORDER BY reject_count DESC;
9) Run-wise analysis

To identify if one particular run generated abnormal rejects.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  run_id,
  COUNT(*) AS reject_count,
  COUNT(DISTINCT entity) AS entity_count,
  COUNT(DISTINCT file_name) AS file_count,
  MIN(extracted_ts) AS first_extract_ts,
  MAX(extracted_ts) AS last_extract_ts
FROM base
GROUP BY run_id
ORDER BY reject_count DESC;
10) Hourly trend analysis

This helps identify spikes within the day.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  TIMESTAMP_TRUNC(extracted_ts, HOUR) AS extract_hour,
  COUNT(*) AS reject_count
FROM base
GROUP BY extract_hour
ORDER BY extract_hour;
11) Daily trend analysis for last 7 days

Good for anomaly/spike view.

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-7 AND CURRENT_DATE()-1
)
SELECT
  CAST(extracted_ts AS DATE) AS extract_dt,
  COUNT(*) AS reject_count
FROM base
GROUP BY extract_dt
ORDER BY extract_dt;
12) Entity trend for last 7 days
WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-7 AND CURRENT_DATE()-1
)
SELECT
  CAST(extracted_ts AS DATE) AS extract_dt,
  entity,
  COUNT(*) AS reject_count
FROM base
GROUP BY extract_dt, entity
ORDER BY extract_dt, reject_count DESC;
13) Null text check

This came up in your earlier discussion. Your lead specifically mentioned null text analysis.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNT(*) AS null_text_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND text IS NULL;

Sample rows:

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND text IS NULL
LIMIT 100;
14) Empty text / blank text check
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNT(*) AS blank_text_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND TRIM(COALESCE(text, '')) = '';
15) Malformed JSON-like text check

Since your text column looks like payload data, check whether it is valid JSON.
If not exactly JSON format, still this query helps identify bad patterns.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNT(*) AS invalid_json_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND text IS NOT NULL
  AND SAFE.PARSE_JSON(text) IS NULL;

Sample invalid rows:

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  file_name,
  run_id,
  text,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND text IS NOT NULL
  AND SAFE.PARSE_JSON(text) IS NULL
LIMIT 100;
16) PK null check
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNT(*) AS null_pk_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND pk_value IS NULL;
17) PK blank check
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNT(*) AS blank_pk_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND TRIM(COALESCE(CAST(pk_value AS STRING), '')) = '';
18) PK datatype anomaly check

Your earlier discussion mentioned safe casting. Use this.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  pk_column,
  pk_value,
  file_name,
  run_id,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND SAFE_CAST(pk_value AS INT64) IS NULL
  AND pk_value IS NOT NULL
LIMIT 500;

Count by entity:

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  COUNT(*) AS invalid_pk_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND SAFE_CAST(pk_value AS INT64) IS NULL
  AND pk_value IS NOT NULL
GROUP BY entity
ORDER BY invalid_pk_count DESC;
19) Duplicate PK inside rejects

This helps identify repeated reject rows for same PK.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  entity,
  pk_column,
  pk_value,
  COUNT(*) AS duplicate_count
FROM base
GROUP BY entity, pk_column, pk_value
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
20) Same PK across multiple files

This is a strong anomaly check.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  entity,
  pk_value,
  COUNT(DISTINCT file_name) AS file_count,
  STRING_AGG(DISTINCT file_name, ', ' LIMIT 10) AS sample_files
FROM base
GROUP BY entity, pk_value
HAVING COUNT(DISTINCT file_name) > 1
ORDER BY file_count DESC;
21) Same PK across multiple run_ids
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
)
SELECT
  entity,
  pk_value,
  COUNT(DISTINCT run_id) AS run_count,
  STRING_AGG(DISTINCT run_id, ', ' LIMIT 10) AS sample_runs
FROM base
GROUP BY entity, pk_value
HAVING COUNT(DISTINCT run_id) > 1
ORDER BY run_count DESC;
22) Mandatory-column related errors

From your screenshot, a key pattern is “mandatory column cannot empty”.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  COUNT(*) AS mandatory_col_issue_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND LOWER(reject_reason) LIKE '%mandatory%'
GROUP BY entity
ORDER BY mandatory_col_issue_count DESC;

Detailed:

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  reject_reason,
  COUNT(*) AS issue_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND LOWER(reject_reason) LIKE '%mandatory%'
GROUP BY entity, reject_reason
ORDER BY issue_count DESC;
23) Reject reason text pattern standardization

Sometimes the same issue appears with slightly different wording.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  LOWER(TRIM(reject_reason)) AS normalized_reject_reason,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
GROUP BY normalized_reject_reason
ORDER BY reject_count DESC;
24) Entity with unusually high reject percentage

If you have the source intake count per entity, compare it.
If not, at least compare each entity’s reject share.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH entity_counts AS (
  SELECT
    entity,
    COUNT(*) AS reject_count
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
  GROUP BY entity
)
SELECT
  entity,
  reject_count,
  ROUND(100 * reject_count / SUM(reject_count) OVER(), 2) AS share_pct
FROM entity_counts
ORDER BY reject_count DESC;
25) Large file anomaly check

Check whether large files are contributing disproportionate rejects.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH file_stats AS (
  SELECT
    file_name,
    MIN(file_size) AS file_size,
    COUNT(*) AS reject_count
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
  GROUP BY file_name
)
SELECT
  file_name,
  file_size,
  reject_count,
  SAFE_DIVIDE(reject_count, file_size) AS reject_per_byte_ratio
FROM file_stats
ORDER BY reject_count DESC;
26) Files with only one reject reason vs multiple reject reasons

This is useful to identify whether a file has one consistent issue or many mixed issues.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH file_reason_stats AS (
  SELECT
    file_name,
    COUNT(*) AS reject_count,
    COUNT(DISTINCT reject_reason) AS distinct_reject_reasons
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
  GROUP BY file_name
)
SELECT *
FROM file_reason_stats
ORDER BY distinct_reject_reasons DESC, reject_count DESC;
27) Top anomalous files by distinct issue types
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH file_reason_stats AS (
  SELECT
    file_name,
    COUNT(*) AS reject_count,
    COUNT(DISTINCT reject_reason) AS distinct_reject_reasons,
    MIN(file_size) AS file_size
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
  GROUP BY file_name
)
SELECT
  *
FROM file_reason_stats
WHERE distinct_reject_reasons > 3
ORDER BY distinct_reject_reasons DESC, reject_count DESC;
28) Most frequent rejected PK columns
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  pk_column,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
GROUP BY pk_column
ORDER BY reject_count DESC;
29) Text length anomaly

Very short or very long payloads may indicate corrupted or incomplete records.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  COUNT(*) AS total_rows,
  MIN(LENGTH(COALESCE(text, ''))) AS min_text_len,
  MAX(LENGTH(COALESCE(text, ''))) AS max_text_len,
  AVG(LENGTH(COALESCE(text, ''))) AS avg_text_len
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
GROUP BY entity
ORDER BY avg_text_len DESC;

Short text rows:

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  file_name,
  run_id,
  pk_value,
  text,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND LENGTH(COALESCE(text, '')) < 20
LIMIT 200;
30) Null pattern by entity
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  COUNTIF(text IS NULL) AS null_text_count,
  COUNTIF(pk_value IS NULL) AS null_pk_count,
  COUNTIF(file_name IS NULL) AS null_file_name_count,
  COUNTIF(run_id IS NULL) AS null_run_id_count,
  COUNT(*) AS total_rows
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
GROUP BY entity
ORDER BY total_rows DESC;
31) Sample 100 rows for manual inspection

Good for documenting actual examples.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  pk_column,
  pk_value,
  file_name,
  file_size,
  extracted_ts,
  run_id,
  text,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
LIMIT 100;
32) Most repeated exact reject payloads

This helps identify systemic duplicate issues.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  reject_reason,
  text,
  COUNT(*) AS repeat_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
GROUP BY entity, reject_reason, text
HAVING COUNT(*) > 1
ORDER BY repeat_count DESC
LIMIT 100;
33) Anomaly check: spike against 7-day average

This is very useful for leadership reporting.

WITH daily_counts AS (
  SELECT
    CAST(extracted_ts AS DATE) AS extract_dt,
    COUNT(*) AS reject_count
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-1
  GROUP BY extract_dt
),
stats AS (
  SELECT
    AVG(reject_count) AS avg_reject_count
  FROM daily_counts
  WHERE extract_dt BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-2
),
current_day AS (
  SELECT
    reject_count
  FROM daily_counts
  WHERE extract_dt = CURRENT_DATE()-1
)
SELECT
  c.reject_count AS current_day_rejects,
  s.avg_reject_count AS prior_avg_rejects,
  ROUND(c.reject_count - s.avg_reject_count, 2) AS diff_from_avg,
  ROUND(100 * SAFE_DIVIDE(c.reject_count - s.avg_reject_count, s.avg_reject_count), 2) AS pct_diff
FROM current_day c
CROSS JOIN stats s;
34) Entity-level anomaly vs prior average
WITH daily_entity_counts AS (
  SELECT
    CAST(extracted_ts AS DATE) AS extract_dt,
    entity,
    COUNT(*) AS reject_count
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-1
  GROUP BY extract_dt, entity
),
historical_avg AS (
  SELECT
    entity,
    AVG(reject_count) AS avg_reject_count
  FROM daily_entity_counts
  WHERE extract_dt BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-2
  GROUP BY entity
),
current_day AS (
  SELECT
    entity,
    reject_count
  FROM daily_entity_counts
  WHERE extract_dt = CURRENT_DATE()-1
)
SELECT
  c.entity,
  c.reject_count AS current_rejects,
  h.avg_reject_count,
  ROUND(c.reject_count - h.avg_reject_count, 2) AS diff,
  ROUND(100 * SAFE_DIVIDE(c.reject_count - h.avg_reject_count, h.avg_reject_count), 2) AS pct_diff
FROM current_day c
LEFT JOIN historical_avg h
  ON c.entity = h.entity
ORDER BY pct_diff DESC, current_rejects DESC;
35) File-level anomaly vs prior average

If same file pattern appears daily.

WITH daily_file_counts AS (
  SELECT
    CAST(extracted_ts AS DATE) AS extract_dt,
    file_name,
    COUNT(*) AS reject_count
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-1
  GROUP BY extract_dt, file_name
),
historical_avg AS (
  SELECT
    file_name,
    AVG(reject_count) AS avg_reject_count
  FROM daily_file_counts
  WHERE extract_dt BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-2
  GROUP BY file_name
),
current_day AS (
  SELECT
    file_name,
    reject_count
  FROM daily_file_counts
  WHERE extract_dt = CURRENT_DATE()-1
)
SELECT
  c.file_name,
  c.reject_count AS current_rejects,
  h.avg_reject_count,
  ROUND(c.reject_count - h.avg_reject_count, 2) AS diff,
  ROUND(100 * SAFE_DIVIDE(c.reject_count - h.avg_reject_count, h.avg_reject_count), 2) AS pct_diff
FROM current_day c
LEFT JOIN historical_avg h
  ON c.file_name = h.file_name
ORDER BY pct_diff DESC, current_rejects DESC;
36) Reconciliation query: source vs target vs reject

This is critical, but you must replace table names.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT 'SOURCE' AS metric, COUNT(*) AS row_count
FROM `project.dataset.source_table`
WHERE CAST(load_dt AS DATE) = v_dt

UNION ALL

SELECT 'TARGET' AS metric, COUNT(*) AS row_count
FROM `project.dataset.target_table`
WHERE CAST(load_dt AS DATE) = v_dt

UNION ALL

SELECT 'REJECT' AS metric, COUNT(*) AS row_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt;

Then validation idea:

Expected source rows = successfully loaded target rows + rejected rows
37) Missing records check using PK

If you know source and target tables.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH src AS (
  SELECT DISTINCT UNT_ID AS pk_value
  FROM `project.dataset.source_table`
  WHERE CAST(load_dt AS DATE) = v_dt
),
tgt AS (
  SELECT DISTINCT UNT_ID AS pk_value
  FROM `project.dataset.target_table`
  WHERE CAST(load_dt AS DATE) = v_dt
),
rej AS (
  SELECT DISTINCT pk_value
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
    AND entity = 'TA_VLN_UNIT_TRANS'
)
SELECT
  s.pk_value
FROM src s
LEFT JOIN tgt t
  ON s.pk_value = t.pk_value
LEFT JOIN rej r
  ON CAST(s.pk_value AS STRING) = CAST(r.pk_value AS STRING)
WHERE t.pk_value IS NULL
  AND r.pk_value IS NULL;

This gives records that are neither loaded nor present in reject — very important anomaly.

38) Which entities have missing records not explained by rejects

This is a bigger reconciliation pattern. You’ll need entity-specific source and target tables.

If you want, later I can tailor these entity-wise.

39) Extract key fields from text if JSON is valid

If your text is valid JSON.

DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  entity,
  JSON_VALUE(text, '$.UNT_ID') AS unt_id,
  JSON_VALUE(text, '$.UNT_KEY_POLICY_NO') AS unt_key_policy_no,
  JSON_VALUE(text, '$.UNT_KEY_CONTR_CD') AS unt_key_contr_cd,
  JSON_VALUE(text, '$.UNT_KEY_BENEFIT_CD') AS unt_key_benefit_cd,
  reject_reason
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
LIMIT 100;
40) Missing field analysis from text payload
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

SELECT
  COUNTIF(JSON_VALUE(text, '$.UNT_ID') IS NULL) AS missing_unt_id,
  COUNTIF(JSON_VALUE(text, '$.UNT_KEY_POLICY_NO') IS NULL) AS missing_policy_no,
  COUNTIF(JSON_VALUE(text, '$.UNT_KEY_CONTR_CD') IS NULL) AS missing_contr_cd,
  COUNTIF(JSON_VALUE(text, '$.UNT_KEY_BENEFIT_CD') IS NULL) AS missing_benefit_cd
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = v_dt
  AND SAFE.PARSE_JSON(text) IS NOT NULL;
41) Top 10 anomaly summary query
DECLARE v_dt DATE DEFAULT CURRENT_DATE()-1;

WITH base AS (
  SELECT *
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) = v_dt
),
dup_pk AS (
  SELECT COUNT(*) AS cnt
  FROM (
    SELECT entity, pk_value
    FROM base
    GROUP BY entity, pk_value
    HAVING COUNT(*) > 1
  )
)
SELECT 'TOTAL_REJECTS' AS metric, CAST(COUNT(*) AS STRING) AS value FROM base
UNION ALL
SELECT 'NULL_TEXT_COUNT', CAST(COUNT(*) AS STRING) FROM base WHERE text IS NULL
UNION ALL
SELECT 'BLANK_TEXT_COUNT', CAST(COUNT(*) AS STRING) FROM base WHERE TRIM(COALESCE(text,'')) = ''
UNION ALL
SELECT 'NULL_PK_COUNT', CAST(COUNT(*) AS STRING) FROM base WHERE pk_value IS NULL
UNION ALL
SELECT 'INVALID_PK_COUNT', CAST(COUNT(*) AS STRING) FROM base WHERE SAFE_CAST(pk_value AS INT64) IS NULL AND pk_value IS NOT NULL
UNION ALL
SELECT 'DISTINCT_REJECT_REASONS', CAST(COUNT(DISTINCT reject_reason) AS STRING) FROM base
UNION ALL
SELECT 'DISTINCT_ENTITIES', CAST(COUNT(DISTINCT entity) AS STRING) FROM base
UNION ALL
SELECT 'DISTINCT_FILES', CAST(COUNT(DISTINCT file_name) AS STRING) FROM base
UNION ALL
SELECT 'DISTINCT_RUNS', CAST(COUNT(DISTINCT run_id) AS STRING) FROM base
UNION ALL
SELECT 'DUPLICATE_PK_GROUPS', CAST(cnt AS STRING) FROM dup_pk;
42) What anomalies you should specifically report

Based on your earlier conversations, these are the anomalies your lead will care about:

Data anomalies

null text

blank text

malformed payload in text

null pk_value

invalid pk_value

duplicate pk_value

same PK in multiple files

same PK in multiple runs

Process anomalies

one file contributing too many rejects

one run contributing too many rejects

spike compared to prior days

entity suddenly showing abnormal reject increase

Business anomalies

mandatory fields missing

records missing from both target and reject

mismatch between source count and target + reject count

43) Excel columns you should maintain

Use this structure for documentation:

Analysis Area	Entity	File Name	Run ID	Reject Reason	Count	Observation	Root Cause	Anomaly Type	Action Needed

And another summary sheet:

Metric	Value
Total Rejects	
Total Entities	
Total Files	
Total Runs	
Null Text Count	
Invalid PK Count	
Duplicate PK Groups	
Top Reject Reason	
Top Problem Entity	
Top Problem File	
44) Suggested final analysis flow for you

Run in this order:

overall summary

reject reason distribution

entity-wise

file-wise

run-wise

null/blank text

PK checks

duplicate PK / repeated file / repeated run

hourly and daily trends

anomaly vs 7-day average

source-target-reject reconciliation

missing records not explained by rejects

document findings in Excel

45) What to say to your lead after analysis

You can summarize like this:

Majority of rejects are coming from specific reject reasons.

Certain entities/files/runs are contributing disproportionately.

Some records show payload quality issues such as null text / malformed structure.

PK-level anomalies exist, including null/invalid/duplicate PKs.

Trend comparison shows whether reject volume is normal or anomalous.

Reconciliation confirms whether missing source records are accounted for in target or reject.

Additional unexplained missing records, if any, need pipeline investigation.

46) Most important note

Because your table is huge, always:

filter by date

use limited sampling when checking raw rows

avoid running full-table heavy queries without partition/date filter

If you want, next I’ll do the most useful thing for you: I can convert all of this into a single organized query document, grouped as:

Summary

Root cause

Anomalies

Reconciliation

Samples

so you can copy-paste one by one in BigQuery easily.

can u print here all the queries with heading ...i want to copy paste it

Perfect 👍 — here is your clean, copy-paste ready query document with clear headings (exactly how you can use in BigQuery / share with your lead).

👉 Replace:

project.dataset.ta_reject_extract_stg

with your actual table if needed.

👉 Replace date if needed:

CURRENT_DATE()-1
=============================
🔹 0. BASE FILTER (USE EVERYWHERE)
=============================
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
=============================
🔹 1. OVERALL SUMMARY
=============================
SELECT 
  COUNT(*) AS total_reject_records,
  COUNT(DISTINCT entity) AS total_entities,
  COUNT(DISTINCT file_name) AS total_files,
  COUNT(DISTINCT run_id) AS total_runs
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1;
=============================
🔹 2. REJECT REASON DISTRIBUTION
=============================
SELECT 
  reject_reason,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY reject_reason
ORDER BY reject_count DESC;
=============================
🔹 3. ENTITY-WISE ANALYSIS
=============================
SELECT 
  entity,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity
ORDER BY reject_count DESC;
=============================
🔹 4. ENTITY + REJECT REASON
=============================
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, reject_reason
ORDER BY reject_count DESC;
=============================
🔹 5. FILE-WISE ANALYSIS
=============================
SELECT 
  file_name,
  COUNT(*) AS reject_count,
  MIN(file_size) AS file_size
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name
ORDER BY reject_count DESC;
=============================
🔹 6. FILE + REJECT REASON
=============================
SELECT 
  file_name,
  reject_reason,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name, reject_reason
ORDER BY reject_count DESC;
=============================
🔹 7. RUN-WISE ANALYSIS
=============================
SELECT 
  run_id,
  COUNT(*) AS reject_count,
  COUNT(DISTINCT file_name) AS file_count,
  COUNT(DISTINCT entity) AS entity_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY run_id
ORDER BY reject_count DESC;
=============================
🔹 8. HOURLY TREND
=============================
SELECT 
  TIMESTAMP_TRUNC(extracted_ts, HOUR) AS hour,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY hour
ORDER BY hour;
=============================
🔹 9. DAILY TREND (7 DAYS)
=============================
SELECT 
  CAST(extracted_ts AS DATE) AS dt,
  COUNT(*) AS reject_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-7 AND CURRENT_DATE()-1
GROUP BY dt
ORDER BY dt;
=============================
🔹 10. NULL TEXT CHECK
=============================
SELECT COUNT(*) AS null_text_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NULL;
=============================
🔹 11. BLANK TEXT CHECK
=============================
SELECT COUNT(*) AS blank_text_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND TRIM(COALESCE(text,'')) = '';
=============================
🔹 12. INVALID JSON CHECK
=============================
SELECT COUNT(*) AS invalid_json_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NOT NULL
  AND SAFE.PARSE_JSON(text) IS NULL;
=============================
🔹 13. NULL PK CHECK
=============================
SELECT COUNT(*) AS null_pk_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND pk_value IS NULL;
=============================
🔹 14. INVALID PK CHECK
=============================
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND SAFE_CAST(pk_value AS INT64) IS NULL
  AND pk_value IS NOT NULL
LIMIT 100;
=============================
🔹 15. DUPLICATE PK CHECK
=============================
SELECT 
  entity,
  pk_value,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, pk_value
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
=============================
🔹 16. SAME PK IN MULTIPLE FILES
=============================
SELECT 
  entity,
  pk_value,
  COUNT(DISTINCT file_name) AS file_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, pk_value
HAVING COUNT(DISTINCT file_name) > 1
ORDER BY file_count DESC;
=============================
🔹 17. SAME PK IN MULTIPLE RUNS
=============================
SELECT 
  entity,
  pk_value,
  COUNT(DISTINCT run_id) AS run_count
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, pk_value
HAVING COUNT(DISTINCT run_id) > 1
ORDER BY run_count DESC;
=============================
🔹 18. MANDATORY COLUMN ISSUES
=============================
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND LOWER(reject_reason) LIKE '%mandatory%'
GROUP BY entity, reject_reason
ORDER BY cnt DESC;
=============================
🔹 19. TEXT LENGTH ANOMALY
=============================
SELECT 
  entity,
  MIN(LENGTH(COALESCE(text,''))) AS min_len,
  MAX(LENGTH(COALESCE(text,''))) AS max_len,
  AVG(LENGTH(COALESCE(text,''))) AS avg_len
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity;
=============================
🔹 20. SHORT TEXT RECORDS
=============================
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND LENGTH(COALESCE(text,'')) < 20
LIMIT 100;
=============================
🔹 21. FILE ANOMALY (MULTIPLE ISSUES)
=============================
SELECT 
  file_name,
  COUNT(*) AS reject_count,
  COUNT(DISTINCT reject_reason) AS issue_types
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name
ORDER BY issue_types DESC, reject_count DESC;
=============================
🔹 22. REJECT REASON NORMALIZATION
=============================
SELECT 
  LOWER(TRIM(reject_reason)) AS normalized_reason,
  COUNT(*) AS cnt
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY normalized_reason
ORDER BY cnt DESC;
=============================
🔹 23. ENTITY ANOMALY (SHARE %)
=============================
SELECT 
  entity,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity
ORDER BY pct DESC;
=============================
🔹 24. SPIKE ANALYSIS (VS 7 DAY AVG)
=============================
WITH daily AS (
  SELECT 
    CAST(extracted_ts AS DATE) AS dt,
    COUNT(*) AS cnt
  FROM `project.dataset.ta_reject_extract_stg`
  WHERE CAST(extracted_ts AS DATE) BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-1
  GROUP BY dt
),
avg_tbl AS (
  SELECT AVG(cnt) AS avg_cnt
  FROM daily
  WHERE dt BETWEEN CURRENT_DATE()-8 AND CURRENT_DATE()-2
),
curr AS (
  SELECT cnt FROM daily WHERE dt = CURRENT_DATE()-1
)
SELECT 
  curr.cnt AS current,
  avg_tbl.avg_cnt AS avg,
  curr.cnt - avg_tbl.avg_cnt AS diff,
  ROUND(100 * SAFE_DIVIDE(curr.cnt - avg_tbl.avg_cnt, avg_tbl.avg_cnt),2) AS pct_diff
FROM curr, avg_tbl;
=============================
🔹 25. TOP ANOMALY SUMMARY
=============================
SELECT 'TOTAL' AS metric, COUNT(*) FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1

UNION ALL

SELECT 'NULL_TEXT', COUNT(*) FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1 AND text IS NULL

UNION ALL

SELECT 'INVALID_PK', COUNT(*) FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1 
AND SAFE_CAST(pk_value AS INT64) IS NULL AND pk_value IS NOT NULL;
=============================
🔹 26. SAMPLE DATA FOR ANALYSIS
=============================
SELECT *
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
LIMIT 100;
=============================
🔹 27. RECONCILIATION (EDIT TABLE NAMES)
=============================
SELECT 'SOURCE', COUNT(*) FROM source_table
UNION ALL
SELECT 'TARGET', COUNT(*) FROM target_table
UNION ALL
SELECT 'REJECT', COUNT(*) 
FROM `project.dataset.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1;
🚀 FINAL NOTE (IMPORTANT)

👉 Run in this order:

Summary

Reject reason

Entity

File

Run

PK checks

Text checks

Trends

Anomalies

Reconciliation

If you want next step 👉
I can convert this into PPT (manager-ready) + Excel sheet with insights filled (very useful for your review).

Replace the project and dataset

Got it 👍 — I can see your actual table from the screenshot.

Your correct table path is:

iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg
❌ Why you got error

Your query:

SELECT FROM `...`

👉 Missing * → BigQuery error:

SELECT list must not be empty

✅ Correct Base Query
SELECT *
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
LIMIT 1000;
🔥 Now I am giving you ALL queries with your actual table (copy-paste ready)
=============================
🔹 1. OVERALL SUMMARY
=============================
SELECT 
  COUNT(*) AS total_reject_records,
  COUNT(DISTINCT entity) AS total_entities,
  COUNT(DISTINCT file_name) AS total_files,
  COUNT(DISTINCT run_id) AS total_runs
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1;
=============================
🔹 2. REJECT REASON DISTRIBUTION
=============================
SELECT 
  reject_reason,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY reject_reason
ORDER BY reject_count DESC;
=============================
🔹 3. ENTITY-WISE ANALYSIS
=============================
SELECT 
  entity,
  COUNT(*) AS reject_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS reject_pct
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity
ORDER BY reject_count DESC;
=============================
🔹 4. FILE-WISE ANALYSIS
=============================
SELECT 
  file_name,
  COUNT(*) AS reject_count,
  MIN(file_size) AS file_size
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY file_name
ORDER BY reject_count DESC;
=============================
🔹 5. RUN-WISE ANALYSIS
=============================
SELECT 
  run_id,
  COUNT(*) AS reject_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY run_id
ORDER BY reject_count DESC;
=============================
🔹 6. NULL TEXT CHECK
=============================
SELECT COUNT(*) AS null_text_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NULL;
=============================
🔹 7. BLANK TEXT CHECK
=============================
SELECT COUNT(*) AS blank_text_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND TRIM(COALESCE(text,'')) = '';
=============================
🔹 8. INVALID JSON CHECK
=============================
SELECT COUNT(*) AS invalid_json_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND text IS NOT NULL
  AND SAFE.PARSE_JSON(text) IS NULL;
=============================
🔹 9. NULL PK CHECK
=============================
SELECT COUNT(*) AS null_pk_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND pk_value IS NULL;
=============================
🔹 10. INVALID PK CHECK
=============================
SELECT *
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND SAFE_CAST(pk_value AS INT64) IS NULL
  AND pk_value IS NOT NULL
LIMIT 100;
=============================
🔹 11. DUPLICATE PK CHECK
=============================
SELECT 
  entity,
  pk_value,
  COUNT(*) AS cnt
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, pk_value
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
=============================
🔹 12. SAME PK MULTIPLE FILES
=============================
SELECT 
  entity,
  pk_value,
  COUNT(DISTINCT file_name) AS file_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity, pk_value
HAVING COUNT(DISTINCT file_name) > 1
ORDER BY file_count DESC;
=============================
🔹 13. MANDATORY COLUMN ISSUES
=============================
SELECT 
  entity,
  reject_reason,
  COUNT(*) AS cnt
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
  AND LOWER(reject_reason) LIKE '%mandatory%'
GROUP BY entity, reject_reason
ORDER BY cnt DESC;
=============================
🔹 14. TEXT LENGTH ANOMALY
=============================
SELECT 
  entity,
  MIN(LENGTH(COALESCE(text,''))) AS min_len,
  MAX(LENGTH(COALESCE(text,''))) AS max_len,
  AVG(LENGTH(COALESCE(text,''))) AS avg_len
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
GROUP BY entity;
=============================
🔹 15. SAMPLE DATA
=============================
SELECT *
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
LIMIT 100;
⚠️ IMPORTANT (VERY IMPORTANT FOR YOU)

👉 Your table:

1.54 TB

1B+ rows

So ALWAYS use:

WHERE CAST(extracted_ts AS DATE) = CURRENT_DATE()-1
🚀 NEXT STEP (Highly Recommended)

Now run these and share results, I will help you convert into:

✅ Root cause summary
✅ Exact anomalies explanation
✅ PPT content for your lead

Just say:
👉 “help me interpret results” 👍

see i want good observations .....querys everything we discussed

Perfect 👍 — now we go to the MOST IMPORTANT PART your lead actually expects:

👉 Not just queries
👉 Strong observations + insights + what to say

I’ll give you ready-made observations templates + how to derive them from queries
(You can literally copy into PPT / Excel)

🎯 1. OVERALL SUMMARY OBSERVATION

👉 From Query: Overall Summary

📌 What to say:

Total reject records for the day: X

Data spans across Y entities, Z files, and N runs

Reject volume is (high/moderate/low) relative to expected load

📌 Insight:

If rejects > 5–10% → ⚠️ potential pipeline/data quality issue

If concentrated in few entities → localized issue

🎯 2. REJECT REASON OBSERVATIONS (MOST IMPORTANT)

👉 From: Reject reason distribution

📌 What to say:

Top reject reason: “mandatory column cannot empty” contributing ~X%

Top 3 reasons contribute ~Y% of total rejects

Remaining reasons are long-tail (low frequency)

📌 Insight:

Indicates data completeness issue at source

Suggests:

Missing mandatory fields

Upstream validation gap

📌 Strong statement (use in PPT):

👉 “Majority of rejects are due to mandatory field violations, indicating upstream data ingestion or validation gaps.”

🎯 3. ENTITY-WISE OBSERVATIONS

👉 From: Entity-wise query

📌 What to say:

Top entity contributing rejects: TA_VLN_UNIT_TRANS (~X%)

Top 2–3 entities contribute majority of failures

📌 Insight:

Problem is not distributed

It is entity-specific

📌 Strong statement:

👉 “Rejects are highly concentrated in specific entities, indicating localized data quality issues rather than systemic failure.”

🎯 4. FILE-WISE OBSERVATIONS

👉 From: File-wise query

📌 What to say:

Top files contributing rejects: File A, File B

These files alone contribute X% of total rejects

📌 Insight:

Indicates:

Specific bad input files

Possibly corrupted or incomplete ingestion

📌 Strong statement:

👉 “A small subset of files contributes disproportionately to rejects, indicating file-level data issues.”

🎯 5. RUN-WISE OBSERVATIONS

👉 From: Run-wise query

📌 What to say:

Run ID XXX generated highest rejects

Rejects are not evenly distributed across runs

📌 Insight:

Indicates:

Batch failure

Pipeline execution issue

📌 Strong statement:

👉 “Certain pipeline runs show abnormal reject volumes, indicating execution or ingestion issues.”

🎯 6. NULL / BLANK TEXT OBSERVATION ⚠️

👉 From: text checks

📌 What to say:

Found X records with NULL text

Found Y records with empty payload

📌 Insight:

Critical issue:

Data not parsed correctly

File ingestion incomplete

📌 Strong statement:

👉 “Presence of null or empty payloads indicates ingestion or parsing failures.”

🎯 7. INVALID JSON OBSERVATION

👉 From: JSON check

📌 What to say:

X% of records have malformed payload

📌 Insight:

Indicates:

Data format inconsistency

Parsing failure in pipeline

📌 Strong statement:

👉 “Malformed payloads suggest upstream data format inconsistencies.”

🎯 8. PRIMARY KEY ANOMALIES 🔥

👉 From: PK queries

📌 What to say:

X records with NULL PK

Y records with invalid PK format

Z duplicate PK groups

📌 Insight:

Very critical:

Data integrity issue

Can break downstream joins

📌 Strong statement:

👉 “Primary key inconsistencies indicate data integrity risks and potential duplication issues.”

🎯 9. DUPLICATE / MULTI-FILE PK ISSUE

👉 From: same PK multiple files

📌 What to say:

Same PK appears across multiple files / runs

📌 Insight:

Indicates:

Reprocessing issues

Duplicate ingestion

📌 Strong statement:

👉 “Duplicate primary keys across files suggest reprocessing or duplicate ingestion anomalies.”

🎯 10. TEXT LENGTH ANOMALY

👉 From: text length query

📌 What to say:

Some records have unusually short payload (<20 chars)

Some records have unusually large payload

📌 Insight:

Short → incomplete data

Large → malformed or nested issues

📌 Strong statement:

👉 “Payload size inconsistencies indicate incomplete or malformed data ingestion.”

🎯 11. TREND / SPIKE OBSERVATION

👉 From: spike query

📌 What to say:

Current reject count vs 7-day average:

Increase of X% OR decrease

📌 Insight:

Spike → anomaly

Stable → normal

📌 Strong statement:

👉 “Reject volume shows (spike/stability), indicating (anomaly/stable pipeline behavior).”

🎯 12. ENTITY ANOMALY (SHARE %)

👉 From: entity %

📌 What to say:

One entity contributes >50% of rejects

📌 Insight:

Major root cause concentrated

📌 Strong statement:

👉 “Reject distribution is skewed, with a single entity dominating failure volume.”

🎯 13. FILE ANOMALY (MULTIPLE ISSUES)

👉 From: file + issue types

📌 What to say:

Some files have multiple reject reasons (3+)

📌 Insight:

Indicates:

Completely bad file

Multiple data issues

📌 Strong statement:

👉 “Certain files exhibit multiple failure types, indicating broader data quality issues.”

🎯 14. RECONCILIATION OBSERVATION 🔥🔥

👉 From: source vs target vs reject

📌 What to say:

Source = X

Target = Y

Reject = Z

📌 Insight:

Check:

X = Y + Z ?
📌 If mismatch:

👉 CRITICAL ISSUE

📌 Strong statement:

👉 “Mismatch between source, target, and reject counts indicates potential data loss or pipeline gaps.”

🎯 15. MISSING RECORDS (MOST ADVANCED)

👉 From PK comparison

📌 What to say:

Some records are neither in target nor reject

📌 Insight:

Critical pipeline gap

📌 Strong statement:

👉 “Certain records are missing from both target and reject datasets, indicating potential data loss during processing.”

🎯 FINAL ROOT CAUSE SUMMARY (YOU CAN SAY THIS DIRECTLY)

👉 Use this as final answer to your lead:

📌 Root Cause Summary

Majority of rejects are due to mandatory column missing issues

Rejects are highly concentrated in specific entities and files

Null and malformed payloads indicate ingestion/parsing issues

Primary key inconsistencies highlight data integrity problems

Duplicate PKs across files/runs suggest reprocessing anomalies

Certain runs and files show abnormal reject spikes

Some records are missing from both target and reject, indicating pipeline gaps

📌 Final Recommendation

Improve upstream data validation

Add mandatory field checks before ingestion

Implement PK validation & deduplication

Fix file-level ingestion issues

Monitor run-level anomalies

Add reconciliation checks in pipeline

🚀 If you want next level (HIGHLY RECOMMENDED)

I can now create:

✅ PPT (ready for manager)
✅ Excel filled with insights
✅ One-page summary for leadership

Just say:
👉 “create PPT” 👍
