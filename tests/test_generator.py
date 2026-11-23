from pathlib import Path

import pytest

from benchmark_lab.data.generator import generate_dataset, iter_transactions
from benchmark_lab.data.schema import REQUIRED_COLUMNS
from benchmark_lab.data.validate import validate_dataset


def test_generator_is_deterministic():
    assert list(iter_transactions(5, seed=9)) == list(iter_transactions(5, seed=9))
    assert list(iter_transactions(5, seed=9)) != list(iter_transactions(5, seed=10))


def test_generate_and_validate_parquet(tmp_path: Path):
    pq = pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "sample.parquet"
    result = generate_dataset(output, rows=101, seed=7, batch_size=20)
    assert result["rows"] == 101
    assert pq.read_table(output).num_rows == 101
    assert tuple(pq.read_schema(output).names) == REQUIRED_COLUMNS
    assert validate_dataset(output)["valid"] is True


def test_generate_and_validate_csv(tmp_path: Path):
    output = tmp_path / "sample.csv"
    generate_dataset(output, rows=25, file_format="csv")
    result = validate_dataset(output)
    assert result["valid"] is True
    assert result["rows"] == 25


def test_reject_non_positive_rows(tmp_path: Path):
    with pytest.raises(ValueError):
        generate_dataset(tmp_path / "bad.parquet", rows=0)


def test_parquet_batching_does_not_change_content(tmp_path: Path):
    pq = pytest.importorskip("pyarrow.parquet")
    small = tmp_path / "small.parquet"
    large = tmp_path / "large.parquet"
    generate_dataset(small, rows=500, seed=11, batch_size=37)
    generate_dataset(large, rows=500, seed=11, batch_size=10_000)
    assert pq.read_table(small).equals(pq.read_table(large))


def test_amounts_are_always_positive():
    assert all(float(row["amount"]) > 0 for row in iter_transactions(2_000, seed=1))
