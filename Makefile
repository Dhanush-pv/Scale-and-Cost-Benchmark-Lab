.PHONY: install test lint sample validate clickhouse-up clickhouse-down

install:
	python -m pip install -e ".[all]"

test:
	pytest -q

lint:
	ruff check src tests

sample:
	benchmark-lab generate --rows 100000 --format parquet --output artifacts/data/transactions.parquet

validate:
	benchmark-lab validate --input artifacts/data/transactions.parquet

clickhouse-up:
	docker compose up -d clickhouse

clickhouse-down:
	docker compose down
