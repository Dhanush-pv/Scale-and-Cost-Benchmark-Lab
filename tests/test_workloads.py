import pytest

from benchmark_lab.workloads.catalog import WORKLOADS, get_workload


def test_workload_ids_are_unique_and_expected():
    ids = [workload.workload_id for workload in WORKLOADS]
    assert len(ids) == len(set(ids))
    assert set(ids) == {"daily_revenue", "merchant_rank", "customer_activity",
                        "country_channel_mix", "hourly_decline_rate"}


def test_workload_lookup():
    assert get_workload("merchant_rank").expected_columns == ("merchant_id", "approved_amount")
    with pytest.raises(KeyError):
        get_workload("not_a_workload")
