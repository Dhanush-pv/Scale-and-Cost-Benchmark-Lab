# Scale and Cost Benchmark Lab


A reproducible engineering lab for comparing analytical workloads across Apache Spark, DuckDB and
ClickHouse. Week 1 builds the foundation: a deterministic synthetic transaction dataset, a
validator, a shared engine-neutral workload contract and a machine-readable benchmark-result
format. Later weeks add engine adapters, scale tests, execution-plan analysis and cost modelling.

## Architecture

```text
Configuration
     |
     v
Synthetic generator ---> Parquet / CSV dataset ---> Dataset validation
                                                |
                                                v
                                      Shared workload contract
                                                |
                         +----------------------+----------------------+
                         |                      |                      |
                      DuckDB                 Spark                ClickHouse
                    (later week)           (later week)            (later week)
                         |                      |                      |
                         +----------------------+----------------------+
                                                |
                                                v
                                  Metrics + JSONL result records
```

## Quick start

Python 3.11+ is required.

```bash
python -m venv .venv
# macOS/Linux:        source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[all]"

# Generate a small local dataset (100,000 rows)
benchmark-lab generate --rows 100000 --format parquet --output artifacts/data/transactions.parquet

# Validate it
benchmark-lab validate --input artifacts/data/transactions.parquet

# Write a metadata-only plan for the workload suite
benchmark-lab plan --input artifacts/data/transactions.parquet --output artifacts/results/plan.json
```

`generate` also accepts `--seed` (default 42) and `--batch-size` (rows per Parquet write batch).
Start small; large runs need a machine with enough disk. A nominal 100 GB target is not a promise
that a laptop can hold it.

Optional ClickHouse service: `docker compose up -d clickhouse` (or `make clickhouse-up`).

## Dataset contract

| Column | Type | Meaning |
|---|---|---|
| transaction_id | string | Stable unique transaction identifier |
| customer_id | string | Synthetic customer identifier |
| merchant_id | string | Synthetic merchant identifier |
| transaction_ts | timestamp (UTC) | UTC event timestamp |
| amount | decimal(12,2) | Positive transaction amount (min 0.01) |
| currency | string | Currency code tied to the generated country |
| country | string | Synthetic two-letter country code |
| channel | string | POS, WEB or MOBILE |
| status | string | APPROVED, DECLINED or REVERSED |
| payment_method | string | CARD, WALLET or BANK_TRANSFER |

Synthetic values are for engineering tests only. They do not represent real customers, merchants
or payments.

## Workload suite

1. `daily_revenue` – daily transaction count and approved amount.
2. `merchant_rank` – top 20 merchants by approved amount.
3. `customer_activity` – customer-level counts, totals and average ticket.
4. `country_channel_mix` – volume and approved amount by country and channel.
5. `hourly_decline_rate` – hourly declined and total counts (decline share = declined / total).

All templates use the same logical column names. Engine-specific SQL adaptations arrive with the
adapters rather than changing the business definition per engine.

## Repository layout

```text
src/benchmark_lab/   generator, validator, workloads, metrics recorder and CLI
configs/             default scale and workload configuration
sql/clickhouse/      ClickHouse table definition
scripts/             convenience scripts
tests/               deterministic unit and CLI tests
docs/                data contract, methodology and verification report
```

## Reproducibility and fair-comparison rules

- Use the same immutable dataset snapshot for every engine.
- Record dataset checksum, row count, file bytes, generator seed and software versions.
- Keep cold-cache and warm-cache measurements separate; run warm-ups separately.
- Report median and p95 latency, not only the fastest run.
- Capture resource limits and hardware details alongside results.
- Do not compare unlike storage formats or query semantics without labelling the difference.
- Cost estimates must state their pricing assumptions and measurement window.

## Development

```bash
make install   # editable install with dev extras
make lint      # ruff check src tests
make test      # pytest -q
```


## License

MIT © Dhanush
