SELECT 1
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
GROUP BY 
    entity, pk_column, pk_value, file_name, file_size, extracted_ts, run_id, text, reject_reason
HAVING COUNT(*) > 1
LIMIT 1;




SELECT COUNT(*) AS duplicate_groups
FROM (
    SELECT 1
    FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
    GROUP BY 
        entity, pk_column, pk_value, file_name, file_size, extracted_ts, run_id, text, reject_reason
    HAVING COUNT(*) > 1
);


SELECT COUNT(*) AS duplicate_groups_sample
FROM (
    SELECT 1
    FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
    TABLESAMPLE SYSTEM (5 PERCENT)
    GROUP BY 
        entity, pk_column, pk_value, file_name, file_size, extracted_ts, run_id, text, reject_reason
    HAVING COUNT(*) > 1
);



SELECT COUNT(*) AS duplicate_groups
FROM (
    SELECT 
        FARM_FINGERPRINT(
            CONCAT(
                IFNULL(entity,''), 
                IFNULL(pk_column,''), 
                IFNULL(CAST(pk_value AS STRING),''), 
                IFNULL(file_name,''), 
                IFNULL(CAST(file_size AS STRING),''), 
                IFNULL(CAST(extracted_ts AS STRING),''), 
                IFNULL(CAST(run_id AS STRING),''), 
                IFNULL(text,''), 
                IFNULL(reject_reason,'')
            )
        ) AS row_hash,
        COUNT(*) AS cnt
    FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
    GROUP BY row_hash
    HAVING COUNT(*) > 1
);
