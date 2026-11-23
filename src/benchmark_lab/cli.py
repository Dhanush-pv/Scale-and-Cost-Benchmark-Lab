"""Command-line interface for Week 1 dataset and benchmark planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark_lab.data.generator import generate_dataset
from benchmark_lab.data.validate import validate_dataset
from benchmark_lab.workloads.catalog import WORKLOADS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="benchmark-lab")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Generate a deterministic synthetic dataset")
    generate.add_argument("--rows", type=int, required=True)
    generate.add_argument("--format", choices=("parquet", "csv"), default="parquet")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--batch-size", type=int, default=50_000,
                          help="Rows per Parquet write batch (bounds memory use)")
    generate.add_argument("--output", required=True)
    validate = commands.add_parser("validate", help="Validate a generated dataset")
    validate.add_argument("--input", required=True)
    plan = commands.add_parser("plan", help="Write a metadata-only workload plan")
    plan.add_argument("--input", required=True)
    plan.add_argument("--output", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "generate":
        result = generate_dataset(args.output, args.rows, args.format, args.seed, args.batch_size)
    elif args.command == "validate":
        result = validate_dataset(args.input)
    else:
        validation = validate_dataset(args.input)
        if not validation["valid"]:
            raise SystemExit(json.dumps(validation, indent=2))
        result = {"dataset": str(Path(args.input)), "validation": validation,
                  "execution_status": "not_run", "workloads": [
                      {"workload_id": item.workload_id, "description": item.description,
                       "sql_template": item.sql, "expected_columns": item.expected_columns}
                      for item in WORKLOADS]}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if args.command == "validate" and not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
