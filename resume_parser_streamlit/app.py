[
  {
    "name": "entity",
    "description": "Source entity/table name from which reject record originated",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "pk_column",
    "description": "Primary key column name extracted from reject record",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "pk_value",
    "description": "Primary key value extracted from reject record",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "reject_file_path",
    "description": "Full GCS path of the reject file",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "file_name",
    "description": "Reject file name only",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "file_size",
    "description": "Size of the reject file in bytes",
    "type": "INT64",
    "mode": "NULLABLE"
  },
  {
    "name": "raw_record",
    "description": "Full raw rejected record for traceability",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "extracted_ts",
    "description": "Timestamp when record was extracted",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "run_id",
    "description": "Unique run identifier for extraction job",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "env",
    "description": "Environment tag (PRE/PROD)",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]