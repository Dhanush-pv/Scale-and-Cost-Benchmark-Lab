"""Dataset structure and invariant validation."""

from __future__ import annotations

import csv
from pathlib import Path

from benchmark_lab.data.schema import (
    ALLOWED_CHANNELS,
    ALLOWED_PAYMENT_METHODS,
    ALLOWED_STATUSES,
    REQUIRED_COLUMNS,
)

MAX_REPORTED_ERRORS = 100


def validate_csv(path: str | Path) -> dict:
    file_path = Path(path)
    errors: list[str] = []
    count = 0
    seen_ids: set[str] = set()
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            return {"valid": False, "rows": 0,
                    "errors": ["Column names or order do not match contract"],
                    "bytes": file_path.stat().st_size}
        for line, row in enumerate(reader, start=2):
            count += 1
            if not row["transaction_id"] or row["transaction_id"] in seen_ids:
                errors.append(f"line {line}: missing or duplicate transaction_id")
            seen_ids.add(row["transaction_id"])
            try:
                if float(row["amount"]) <= 0:
                    errors.append(f"line {line}: amount must be positive")
            except ValueError:
                errors.append(f"line {line}: amount is not numeric")
            if row["channel"] not in ALLOWED_CHANNELS:
                errors.append(f"line {line}: invalid channel")
            if row["status"] not in ALLOWED_STATUSES:
                errors.append(f"line {line}: invalid status")
            if row["payment_method"] not in ALLOWED_PAYMENT_METHODS:
                errors.append(f"line {line}: invalid payment_method")
            if not row["transaction_ts"].endswith("Z"):
                errors.append(f"line {line}: transaction_ts must be UTC (Z suffix)")
            if len(errors) >= MAX_REPORTED_ERRORS:
                errors.append(f"validation stopped after {MAX_REPORTED_ERRORS} errors")
                break
    return {"valid": not errors, "rows": count, "errors": errors,
            "bytes": file_path.stat().st_size}


def validate_parquet(path: str | Path) -> dict:
    """Check column names/order, Arrow types and per-batch row invariants.

    Row-level checks stream record batches so memory stays bounded. Uniqueness of
    ``transaction_id`` is a CSV-only check in Week 1 (it needs a global set).
    """
    try:
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "Parquet validation requires pyarrow; install with `pip install pyarrow`"
        ) from exc

    file_path = Path(path)
    parquet = pq.ParquetFile(file_path)
    schema = parquet.schema_arrow
    names = tuple(schema.names)
    if names != REQUIRED_COLUMNS:
        return {"valid": False, "rows": parquet.metadata.num_rows,
                "errors": ["Column names or order do not match contract"],
                "bytes": file_path.stat().st_size, "columns": list(names)}

    errors: list[str] = []
    if not pa.types.is_timestamp(schema.field("transaction_ts").type) or \
            schema.field("transaction_ts").type.tz != "UTC":
        errors.append("transaction_ts must be a UTC timestamp")
    amount_type = schema.field("amount").type
    if not pa.types.is_decimal(amount_type):
        errors.append("amount must be a decimal column")
    for name in REQUIRED_COLUMNS:
        if name not in ("transaction_ts", "amount") and not (
            pa.types.is_string(schema.field(name).type)
            or pa.types.is_large_string(schema.field(name).type)
        ):
            errors.append(f"{name} must be a string column")

    if not errors:
        allowed = {"channel": ALLOWED_CHANNELS, "status": ALLOWED_STATUSES,
                   "payment_method": ALLOWED_PAYMENT_METHODS}
        for batch in parquet.iter_batches(batch_size=100_000):
            for name in REQUIRED_COLUMNS:
                nulls = batch.column(name).null_count
                if nulls:
                    errors.append(f"{name}: {nulls} null value(s) in a batch")
            non_positive = pc.sum(pc.cast(pc.less_equal(
                batch.column("amount"), pa.scalar(0, amount_type)), pa.int64())).as_py() or 0
            if non_positive:
                errors.append(f"amount: {non_positive} non-positive value(s) in a batch")
            for name, values in allowed.items():
                bad = pc.invert(pc.is_in(batch.column(name), value_set=pa.array(sorted(values))))
                bad_count = pc.sum(pc.cast(bad, pa.int64())).as_py() or 0
                if bad_count:
                    errors.append(f"{name}: {bad_count} value(s) outside allowed set in a batch")
            if len(errors) >= MAX_REPORTED_ERRORS:
                errors.append(f"validation stopped after {MAX_REPORTED_ERRORS} errors")
                break

    return {"valid": not errors, "rows": parquet.metadata.num_rows, "errors": errors,
            "bytes": file_path.stat().st_size, "columns": list(names)}


def validate_dataset(path: str | Path) -> dict:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        return validate_csv(file_path)
    if file_path.suffix.lower() == ".parquet":
        return validate_parquet(file_path)
    raise ValueError("Only .csv and .parquet datasets are supported")
