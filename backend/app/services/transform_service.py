"""
Data transformation pipeline: CSV→Parquet, JSON normalization, PII masking.
"""
import io
import re
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


# PII fields to mask (common enterprise patterns)
_PII_COLUMNS = {
    "email", "phone", "ssn", "social_security", "credit_card",
    "card_number", "dob", "date_of_birth", "passport", "address",
}

_PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN REDACTED]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[CARD REDACTED]"),
]


def csv_to_parquet(data: bytes, config: Optional[dict] = None) -> bytes:
    """Convert CSV bytes to Parquet bytes."""
    config = config or {}
    df = pd.read_csv(io.BytesIO(data), **config.get("read_options", {}))
    logger.info(f"CSV→Parquet: {len(df)} rows, {len(df.columns)} columns")
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    return buf.getvalue()


def json_normalize(data: bytes, config: Optional[dict] = None) -> bytes:
    """Flatten nested JSON into a CSV."""
    import json
    config = config or {}
    raw = json.loads(data)
    records = raw if isinstance(raw, list) else [raw]
    record_path = config.get("record_path")
    df = pd.json_normalize(records, record_path=record_path) if record_path else pd.json_normalize(records)
    logger.info(f"JSON normalize: {len(df)} rows")
    return df.to_csv(index=False).encode()


def mask_pii(data: bytes, config: Optional[dict] = None) -> bytes:
    """
    Mask PII fields in CSV data.
    Masks entire columns whose names match known PII fields,
    and applies regex patterns to string columns.
    """
    config = config or {}
    df = pd.read_csv(io.BytesIO(data))

    pii_cols_override = set(config.get("pii_columns", []))
    cols_to_mask = pii_cols_override or {c.lower() for c in df.columns if c.lower() in _PII_COLUMNS}

    for col in df.columns:
        if col.lower() in cols_to_mask:
            df[col] = "[REDACTED]"
        elif df[col].dtype == object:
            for pattern, replacement in _PII_PATTERNS:
                df[col] = df[col].astype(str).str.replace(pattern, replacement, regex=True)

    masked_count = len(cols_to_mask)
    logger.info(f"PII mask: masked {masked_count} columns")
    return df.to_csv(index=False).encode()


def apply_transform(data: bytes, transform_type: str, config: Optional[dict] = None) -> tuple[bytes, str]:
    """
    Apply a named transform. Returns (transformed_bytes, new_file_extension).
    """
    if transform_type == "csv_to_parquet":
        return csv_to_parquet(data, config), ".parquet"
    elif transform_type == "json_normalize":
        return json_normalize(data, config), ".csv"
    elif transform_type == "pii_mask":
        return mask_pii(data, config), ".csv"
    else:
        return data, ""
