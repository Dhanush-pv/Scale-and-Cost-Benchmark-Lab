import csv
from pathlib import Path

import pytest

from benchmark_lab.data.generator import generate_dataset
from benchmark_lab.data.schema import REQUIRED_COLUMNS
from benchmark_lab.data.validate import validate_dataset


def _rewrite_csv(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_csv_detects_duplicate_ids_and_bad_values(tmp_path: Path):
    output = tmp_path / "bad.csv"
    generate_dataset(output, rows=10, file_format="csv")

    def corrupt(rows):
        rows[1]["transaction_id"] = rows[0]["transaction_id"]
        rows[2]["status"] = "UNKNOWN"
        rows[3]["amount"] = "-1.00"

    _rewrite_csv(output, corrupt)
    result = validate_dataset(output)
    assert result["valid"] is False
    joined = " ".join(result["errors"])
    assert "duplicate transaction_id" in joined
    assert "invalid status" in joined
    assert "amount must be positive" in joined


def test_csv_rejects_wrong_columns(tmp_path: Path):
    output = tmp_path / "wrong.csv"
    output.write_text("a,b\n1,2\n", encoding="utf-8")
    assert validate_dataset(output)["valid"] is False


def test_parquet_rejects_wrong_schema(tmp_path: Path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "wrong.parquet"
    pq.write_table(pa.table({name: ["x"] for name in REQUIRED_COLUMNS}), output)
    result = validate_dataset(output)
    assert result["valid"] is False
    assert any("transaction_ts" in e or "amount" in e for e in result["errors"])


def test_parquet_rejects_invalid_enum(tmp_path: Path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    good = tmp_path / "good.parquet"
    generate_dataset(good, rows=50, seed=3)
    table = pq.read_table(good)
    idx = table.schema.get_field_index("channel")
    table = table.set_column(idx, "channel", pa.array(["FAX"] * table.num_rows))
    bad = tmp_path / "bad.parquet"
    pq.write_table(table, bad)
    result = validate_dataset(bad)
    assert result["valid"] is False
    assert any("channel" in e for e in result["errors"])


def test_unsupported_extension(tmp_path: Path):
    path = tmp_path / "data.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_dataset(path)
