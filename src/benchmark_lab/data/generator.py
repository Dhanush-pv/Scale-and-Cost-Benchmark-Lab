"""Deterministic synthetic transaction data generation."""

from __future__ import annotations

import csv
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from benchmark_lab.data.schema import REQUIRED_COLUMNS

COUNTRIES = ("DE", "US", "GB", "IN", "FR", "NL", "ES", "CA")
CURRENCIES = ("EUR", "USD", "GBP", "INR", "EUR", "EUR", "EUR", "CAD")
CHANNELS = ("POS", "WEB", "MOBILE")
STATUSES = ("APPROVED", "DECLINED", "REVERSED")
METHODS = ("CARD", "WALLET", "BANK_TRANSFER")
BASE_TS = datetime(2024, 1, 1, tzinfo=UTC)
MIN_AMOUNT = Decimal("0.01")


def iter_transactions(rows: int, seed: int = 42):
    """Yield deterministic synthetic rows without holding the whole dataset in memory."""
    if rows < 1:
        raise ValueError("rows must be at least 1")
    rng = random.Random(seed)
    for index in range(rows):
        country_index = rng.randrange(len(COUNTRIES))
        timestamp = BASE_TS + timedelta(seconds=rng.randrange(366 * 24 * 60 * 60))
        # A mild heavy tail creates realistic skew without claiming to model a real market.
        amount = min(5000.0, rng.lognormvariate(3.2, 1.0))
        amount_dec = max(MIN_AMOUNT, Decimal(str(amount)).quantize(Decimal("0.01")))
        yield {
            "transaction_id": f"txn_{index:012d}",
            "customer_id": f"cust_{rng.randrange(max(100, rows // 8)):08d}",
            "merchant_id": f"merch_{rng.randrange(max(25, rows // 200)):06d}",
            "transaction_ts": timestamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "amount": f"{amount_dec:.2f}",
            "currency": CURRENCIES[country_index],
            "country": COUNTRIES[country_index],
            "channel": rng.choice(CHANNELS),
            "status": rng.choices(STATUSES, weights=(0.91, 0.07, 0.02), k=1)[0],
            "payment_method": rng.choice(METHODS),
        }


def _parquet_schema():
    import pyarrow as pa

    return pa.schema([
        ("transaction_id", pa.string()), ("customer_id", pa.string()),
        ("merchant_id", pa.string()), ("transaction_ts", pa.timestamp("us", tz="UTC")),
        ("amount", pa.decimal128(12, 2)), ("currency", pa.string()),
        ("country", pa.string()), ("channel", pa.string()), ("status", pa.string()),
        ("payment_method", pa.string()),
    ])


def _to_arrow_table(batch: list[dict], schema):
    import pyarrow as pa

    converted = [
        {
            **row,
            "transaction_ts": datetime.fromisoformat(row["transaction_ts"].replace("Z", "+00:00")),
            "amount": Decimal(row["amount"]),
        }
        for row in batch
    ]
    return pa.Table.from_pylist(converted, schema=schema)


def generate_dataset(output: str | Path, rows: int, file_format: str = "parquet", seed: int = 42,
                     batch_size: int = 50_000) -> dict:
    """Write Parquet incrementally or CSV with a stable column order."""
    path = Path(output)
    if file_format not in {"parquet", "csv"}:
        raise ValueError("file_format must be 'parquet' or 'csv'")
    if rows < 1 or batch_size < 1:
        raise ValueError("rows and batch_size must be positive")
    path.parent.mkdir(parents=True, exist_ok=True)

    if file_format == "csv":
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(iter_transactions(rows, seed))
    else:
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise RuntimeError(
                "Parquet output requires pyarrow; install with `pip install pyarrow`"
            ) from exc
        schema = _parquet_schema()
        batch: list[dict] = []
        with pq.ParquetWriter(path, schema, compression="zstd") as writer:
            for record in iter_transactions(rows, seed):
                batch.append(record)
                if len(batch) >= batch_size:
                    writer.write_table(_to_arrow_table(batch, schema))
                    batch.clear()
            if batch:
                writer.write_table(_to_arrow_table(batch, schema))

    return {"path": str(path), "rows": rows, "format": file_format, "bytes": path.stat().st_size,
            "seed": seed, "batch_size": batch_size}
