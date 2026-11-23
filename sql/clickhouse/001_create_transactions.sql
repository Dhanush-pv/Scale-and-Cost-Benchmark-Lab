CREATE DATABASE IF NOT EXISTS benchmark_lab;

CREATE TABLE IF NOT EXISTS benchmark_lab.transactions
(
    transaction_id String,
    customer_id String,
    merchant_id String,
    transaction_ts DateTime64(0, 'UTC'),
    amount Decimal(12, 2),
    currency LowCardinality(String),
    country LowCardinality(String),
    channel LowCardinality(String),
    status LowCardinality(String),
    payment_method LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(transaction_ts)
ORDER BY (transaction_ts, country, merchant_id, transaction_id);
