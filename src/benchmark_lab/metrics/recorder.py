"""Portable benchmark timing, process-memory and result recording."""

from __future__ import annotations

import hashlib
import json
import platform
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psutil

JSON_TYPES = (dict, list, str, int, float, type(None))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def measure_callable(fn: Callable[[], Any], dataset_path: str | Path, workload_id: str,
                     engine: str = "not_run", iteration: int = 1) -> dict:
    process = psutil.Process()
    rss_before = process.memory_info().rss
    started = time.perf_counter()
    result = fn()
    elapsed_ms = (time.perf_counter() - started) * 1000
    rss_after = process.memory_info().rss
    path = Path(dataset_path)
    return {
        "workload_id": workload_id,
        "engine": engine,
        "iteration": iteration,
        "status": "success",
        "elapsed_ms": round(elapsed_ms, 3),
        "process_rss_before_bytes": rss_before,
        "process_rss_after_bytes": rss_after,
        "process_rss_delta_bytes": rss_after - rss_before,
        "dataset_path": str(path),
        "dataset_bytes": path.stat().st_size,
        "dataset_sha256": sha256_file(path),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "result_metadata": result if isinstance(result, JSON_TYPES) else None,
    }


def append_jsonl(record: dict, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
