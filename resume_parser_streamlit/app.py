SELECT COUNT(*) AS null_pk_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE primary_key IS NULL;



SELECT COUNT(*) AS invalid_pk_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE SAFE_CAST(primary_key AS INT64) IS NULL
AND primary_key IS NOT NULL;

SELECT primary_key, COUNT(*) AS cnt
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE primary_key IS NOT NULL
GROUP BY primary_key
HAVING COUNT(*) > 1
ORDER BY cnt DESC;



SELECT primary_key,
       MIN(DATE(ingestion_date)) AS first_seen,
       MAX(DATE(ingestion_date)) AS last_seen,
       COUNT(*) AS total_rejections
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
WHERE primary_key IS NOT NULL
GROUP BY primary_key
HAVING COUNT(*) > 1
ORDER BY total_rejections DESC;



WITH dedup_reject AS (
  SELECT *
  FROM (
    SELECT *,
           ROW_NUMBER() OVER (
             PARTITION BY primary_key
             ORDER BY ingestion_date DESC
           ) AS rn
    FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
    WHERE primary_key IS NOT NULL
  )
  WHERE rn = 1
)
SELECT COUNT(*) FROM dedup_reject;
