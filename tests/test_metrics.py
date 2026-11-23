import json
from pathlib import Path

from benchmark_lab.metrics.recorder import append_jsonl, measure_callable, sha256_file


def test_result_record_contains_reproducibility_metadata(tmp_path: Path):
    dataset = tmp_path / "input.txt"
    dataset.write_text("benchmark fixture", encoding="utf-8")
    record = measure_callable(lambda: {"rows": 3}, dataset, "fixture_query", engine="test")
    assert record["status"] == "success"
    assert record["dataset_sha256"] == sha256_file(dataset)
    assert record["elapsed_ms"] >= 0
    output = tmp_path / "results.jsonl"
    append_jsonl(record, output)
    assert json.loads(output.read_text(encoding="utf-8"))["workload_id"] == "fixture_query"
