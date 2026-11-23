"""Canonical workload definitions; engine adapters translate these semantics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    workload_id: str
    description: str
    sql: str
    expected_columns: tuple[str, ...]


WORKLOADS = (
    Workload("daily_revenue", "Daily transaction volume and approved amount",
             "SELECT CAST(transaction_ts AS DATE) AS event_date, COUNT(*) AS transaction_count, "
             "SUM(CASE WHEN status = 'APPROVED' THEN amount ELSE 0 END) AS approved_amount "
             "FROM transactions "
             "GROUP BY event_date ORDER BY event_date",
             ("event_date", "transaction_count", "approved_amount")),
    Workload("merchant_rank", "Top 20 merchants by approved amount",
             "SELECT merchant_id, SUM(amount) AS approved_amount FROM transactions "
             "WHERE status = 'APPROVED' GROUP BY merchant_id "
             "ORDER BY approved_amount DESC LIMIT 20",
             ("merchant_id", "approved_amount")),
    Workload("customer_activity", "Customer-level activity and average ticket",
             "SELECT customer_id, COUNT(*) AS transaction_count, SUM(amount) AS total_amount, "
             "AVG(amount) AS average_ticket FROM transactions GROUP BY customer_id",
             ("customer_id", "transaction_count", "total_amount", "average_ticket")),
    Workload("country_channel_mix", "Volume and approved amount by country and channel",
             "SELECT country, channel, COUNT(*) AS transaction_count, "
             "SUM(CASE WHEN status = 'APPROVED' THEN amount ELSE 0 END) AS approved_amount "
             "FROM transactions "
             "GROUP BY country, channel ORDER BY country, channel",
             ("country", "channel", "transaction_count", "approved_amount")),
    Workload("hourly_decline_rate", "Hourly declined transaction share",
             "SELECT DATE_TRUNC('hour', transaction_ts) AS event_hour, "
             "SUM(CASE WHEN status = 'DECLINED' THEN 1 ELSE 0 END) AS declined_count, "
             "COUNT(*) AS transaction_count FROM transactions "
             "GROUP BY event_hour ORDER BY event_hour",
             ("event_hour", "declined_count", "transaction_count")),
)


def get_workload(workload_id: str) -> Workload:
    for workload in WORKLOADS:
        if workload.workload_id == workload_id:
            return workload
    raise KeyError(f"Unknown workload: {workload_id}")
