SELECT 
    *,
    COUNT(*) OVER (PARTITION BY 
        entity,
        pk_column,
        pk_value,
        file_name,
        file_size,
        extracted_ts,
        run_id,
        text,
        reject_reason
    ) AS duplicate_count
FROM `iw-gid-prd-01-c683.gid_brd_staging_backup.ta_reject_extract_stg`
QUALIFY duplicate_count > 1;
