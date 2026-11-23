"""Convenience entry point for generating a 100k-row sample."""
from benchmark_lab.data.generator import generate_dataset

if __name__ == "__main__":
    print(generate_dataset("artifacts/data/transactions.parquet", rows=100_000,
                           file_format="parquet", seed=42))
