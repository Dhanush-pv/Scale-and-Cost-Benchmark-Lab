"""Canonical transaction schema shared by all benchmark engines."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    name: str
    logical_type: str
    nullable: bool = False


TRANSACTION_SCHEMA = (
    Field("transaction_id", "string"),
    Field("customer_id", "string"),
    Field("merchant_id", "string"),
    Field("transaction_ts", "timestamp_utc"),
    Field("amount", "decimal(12,2)"),
    Field("currency", "string"),
    Field("country", "string"),
    Field("channel", "string"),
    Field("status", "string"),
    Field("payment_method", "string"),
)

REQUIRED_COLUMNS = tuple(field.name for field in TRANSACTION_SCHEMA)
ALLOWED_CHANNELS = {"POS", "WEB", "MOBILE"}
ALLOWED_STATUSES = {"APPROVED", "DECLINED", "REVERSED"}
ALLOWED_PAYMENT_METHODS = {"CARD", "WALLET", "BANK_TRANSFER"}
