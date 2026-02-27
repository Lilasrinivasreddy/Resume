#!/usr/bin/env python3

import os
import re
import sys
import time
import queue
import logging
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor

# >>> ADDED: BigQuery + timestamp support
from google.cloud import bigquery
from datetime import datetime


# --------------------------------------------------
# CONFIG (env vars override)
# --------------------------------------------------

INPUT_FILE = os.getenv("INPUT_FILE", "hist_reject_paths.txt")

# >>> REMOVED: OUTPUT_FILE not needed (CSV output removed)
# OUTPUT_FILE = os.getenv("OUTPUT_FILE", "extracted_first_id.csv")

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "16"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "2.0"))

# >>> ADDED: BigQuery target table (matches your existing schema/table)
BQ_PROJECT = os.getenv("BQ_PROJECT", "iw-gid-pre-01-ab84")
BQ_DATASET = os.getenv("BQ_DATASET", "gid_brd_staging_backup")
BQ_TABLE = os.getenv("BQ_TABLE", "ta_reject_extract_stg")

# >>> ADDED: run_id for tracing this execution (matches your schema)
RUN_ID = os.getenv("RUN_ID", f"run_{int(time.time())}")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# --------------------------------------------------
# PATTERNS
# --------------------------------------------------

# Match a full Rec block as a JSON-like string:
# 'Rec': {...}
REC_PATTERN = re.compile(r"""'Rec'\s*:\s*({.*?})""", re.DOTALL | re.MULTILINE)

# Extract the FIRST key/value from the start of the object
FIRST_KV_PATTERN = re.compile(
    r'^\{\s*"([^"]+)"\s*:\s*(?:"([^"]*)"|([0-9]+))',
    re.DOTALL,
)

# >>> ADDED: Extract reject reason from reject content
# Works for patterns like:
# "Reason": "...."  OR  RejectReason: '....' OR Error="...."
REJECT_REASON_PATTERN = re.compile(
    r"(?:Reason|RejectReason|Error)\s*[:=]\s*['\"]?(.*?)['\"]?(?:,|\n|})",
    re.IGNORECASE | re.DOTALL,
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def derive_entity(gcs_path: str) -> str:
    parts = gcs_path.split("/")
    return parts[-3].upper() if len(parts) >= 5 else "UNKNOWN"


def stream_lines_via_gsutil(gcs_path: str):
    """
    Stream a file from GCS using gsutil cat to avoid downloading to local disk.
    """
    proc = subprocess.Popen(
        ["gsutil", "cat", gcs_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )
    try:
        for line in proc.stdout:
            yield line.rstrip("\r\n")
    finally:
        _ = proc.stderr.read()
        proc.wait()


def extract_first_id_from_rec(rec_json_text: str):
    """
    Returns (key, value) for the FIRST key/value pair in the object
    without strict JSON parsing (works even if text is not perfect JSON).
    """
    m = FIRST_KV_PATTERN.search(rec_json_text)
    if not m:
        return None, None
    key = m.group(1)
    val = m.group(2) if m.group(2) is not None else m.group(3)
    return key, val


# >>> ADDED: reject reason extractor
def extract_reject_reason(text: str) -> str:
    m = REJECT_REASON_PATTERN.search(text)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


# >>> ADDED: get file size from gsutil ls -l (matches your schema column file_size)
def get_gcs_file_size(gcs_path: str):
    try:
        out = subprocess.check_output(["gsutil", "ls", "-l", gcs_path], text=True)
        # output looks like: "<size>  <timestamp>  gs://bucket/path"
        size_str = out.strip().split()[0]
        return int(size_str) if size_str.isdigit() else None
    except Exception:
        return None


# --------------------------------------------------
# PROCESS A SINGLE REJECT FILE
# --------------------------------------------------

def process_file(gcs_path: str, writer_q: queue.Queue, progress_q: queue.Queue):
    """
    Reads reject file from GCS, extracts (entity, pk_column, pk_value, reject_reason)
    and pushes rows into writer queue (BQ loader thread).
    """

    entity = derive_entity(gcs_path)
    records_scanned = 0
    ids_emitted = 0

    # >>> ADDED: file_size extracted once per file
    file_size = get_gcs_file_size(gcs_path)

    buffer = []

    for raw_line in stream_lines_via_gsutil(gcs_path):
        line = raw_line.replace("\r", "")
        buffer.append(line)

        joined = "\n".join(buffer)

        matches = list(REC_PATTERN.finditer(joined))
        if matches:
            last_end = 0
            for m in matches:
                rec_text = m.group(1)
                records_scanned += 1

                key, val = extract_first_id_from_rec(rec_text)

                # >>> ADDED: reject_reason extraction (lead asked)
                reject_reason = extract_reject_reason(joined)

                if key and val:
                    # >>> CHANGED: queue payload is dict matching your BQ schema
                    writer_q.put({
                        "entity": entity,
                        "pk_column": key,
                        "pk_value": str(val),
                        "file_name": gcs_path.split("/")[-1],
                        "file_size": file_size,
                        "extracted_ts": datetime.utcnow().isoformat(),
                        "run_id": RUN_ID,
                        "reject_reason": reject_reason,   # NEW column to be added in BQ
                    })
                    ids_emitted += 1

                last_end = m.end()

            tail = joined[last_end:]
            buffer = [tail] if tail else []

        else:
            # Safety: bound buffer growth if no matches for a long time
            if len(joined) > 10_000_000:
                buffer = [joined[-1_000_000:]]

    progress_q.put(("file_done", gcs_path, records_scanned, ids_emitted))


# --------------------------------------------------
# BQ WRITER THREAD (replaces CSV writer)
# --------------------------------------------------

# >>> CHANGED: Entire writer thread now inserts into BigQuery
def writer_thread_fn(writer_q: queue.Queue, stop_event: threading.Event):
    client = bigquery.Client(project=BQ_PROJECT)
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    batch = []
    BATCH_SIZE = 500
    last_flush = time.time()

    while not stop_event.is_set() or not writer_q.empty():
        try:
            row = writer_q.get(timeout=0.2)
            batch.append(row)
        except queue.Empty:
            pass

        # Flush by batch size or time interval
        if batch and (len(batch) >= BATCH_SIZE or (time.time() - last_flush) >= FLUSH_INTERVAL):
            errors = client.insert_rows_json(table_id, batch)
            if errors:
                logging.error("BQ insert errors: %s", errors)
            batch.clear()
            last_flush = time.time()

    # Final flush
    if batch:
        errors = client.insert_rows_json(table_id, batch)
        if errors:
            logging.error("Final BQ insert errors: %s", errors)


# --------------------------------------------------
# READ INPUT PATH LIST FILE
# --------------------------------------------------

def read_paths(input_file: str):
    paths = []
    with open(input_file, "r") as f:
        for raw in f:
            s = raw.strip()
            if not s or s == "File Path":
                continue

            # Keep only leading gs://... up to first whitespace
            if "gs://" in s:
                start = s.find("gs://")
                end = len(s)
                for i, ch in enumerate(s[start:], start=start):
                    if ch.isspace():
                        end = i
                        break
                s = s[start:end]

            if s.startswith("gs://"):
                paths.append(s)

    return paths


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    paths = read_paths(INPUT_FILE)
    if not paths:
        logging.error("No valid paths in %s", INPUT_FILE)
        sys.exit(1)

    logging.info("Starting processing of %d files with MAX_WORKERS=%d", len(paths), MAX_WORKERS)
    logging.info("Writing output to BigQuery table: %s.%s.%s | run_id=%s", BQ_PROJECT, BQ_DATASET, BQ_TABLE, RUN_ID)

    writer_q = queue.Queue(maxsize=10000)
    progress_q = queue.Queue()
    stop_event = threading.Event()

    # >>> CHANGED: writer thread no longer takes OUTPUT_FILE
    wt = threading.Thread(target=writer_thread_fn, args=(writer_q, stop_event), daemon=True)
    wt.start()

    total_files = len(paths)
    files_done = 0
    total_records = 0
    total_ids = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(process_file, p, writer_q, progress_q) for p in paths]

        remaining = total_files
        while remaining:
            try:
                kind, gcs_path, recs, ids = progress_q.get(timeout=0.5)
            except queue.Empty:
                remaining = sum(1 for f in futures if not f.done())
                continue

            if kind == "file_done":
                files_done += 1
                total_records += recs
                total_ids += ids

                logging.info(
                    "Done: %s | records=%d ids=%d | progress %d/%d",
                    gcs_path, recs, ids, files_done, total_files
                )

    stop_event.set()
    wt.join(timeout=10)

    logging.info("Completed. Files=%d Records=%d IDs=%d", files_done, total_records, total_ids)


if __name__ == "__main__":
    main()
