"""
Data Normalization Layer for Custom Transaction Ingestion.
Maps arbitrary column aliases, standardizes datetime formats, parses currency/amount strings,
and normalizes records into canonical Transaction models.
"""
from datetime import datetime
import re
from typing import Dict, Any, List, Optional, Tuple
from dateutil import parser as date_parser

from backend.models.transaction import Transaction, PaymentChannel, TransactionType, TransactionStatus


COLUMN_ALIASES: Dict[str, List[str]] = {
    "transaction_id": ["transaction_id", "txn_id", "tx_id", "transaction", "id", "reference", "ref_id", "trans_id"],
    "sender": ["sender", "sender_account", "source", "source_account", "from", "from_account", "originator", "sender_id", "source_acc", "from_acc"],
    "receiver": ["receiver", "receiver_account", "destination", "destination_account", "to", "to_account", "beneficiary", "receiver_id", "dest_acc", "to_acc"],
    "amount": ["amount", "amt", "value", "transaction_amount", "txn_amount", "sum", "total"],
    "timestamp": ["timestamp", "date", "datetime", "time", "transaction_time", "txn_time", "created_at", "trans_date"],
    "currency": ["currency", "curr", "currency_code"],
    "channel": ["channel", "payment_channel", "mode", "payment_mode", "txn_channel", "payment_type"],
    "remarks": ["remarks", "description", "narration", "note", "purpose", "memo"],
}


def map_column_headers(headers: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Maps detected CSV/JSON headers to canonical field names.
    Returns (header_to_canonical_map, list_of_missing_required_fields).
    """
    cleaned_headers = [h.strip().lower().replace(" ", "_").replace("-", "_") for h in headers]
    header_map: Dict[str, str] = {}

    for orig_header, clean in zip(headers, cleaned_headers):
        matched = False
        for canonical, aliases in COLUMN_ALIASES.items():
            if clean in aliases or any(clean.startswith(a) or clean.endswith(a) for a in aliases):
                header_map[orig_header] = canonical
                matched = True
                break
        if not matched:
            header_map[orig_header] = clean

    # Check required fields: transaction_id, sender, receiver, amount, timestamp
    mapped_canonicals = set(header_map.values())
    required = ["transaction_id", "sender", "receiver", "amount", "timestamp"]
    missing = [req for req in required if req not in mapped_canonicals]

    return header_map, missing


def parse_flexible_timestamp(val: Any) -> Optional[datetime]:
    """Parses arbitrary timestamp formats into standard UTC/local datetime."""
    if val is None or str(val).strip() == "":
        return None

    if isinstance(val, datetime):
        return val

    val_str = str(val).strip()

    # Try numeric epoch timestamp
    if val_str.isdigit():
        epoch_val = int(val_str)
        if epoch_val > 1000000000000:  # milliseconds
            return datetime.utcfromtimestamp(epoch_val / 1000.0)
        elif epoch_val > 1000000000:  # seconds
            return datetime.utcfromtimestamp(epoch_val)

    try:
        return date_parser.parse(val_str)
    except Exception:
        return None


def parse_flexible_amount(val: Any) -> Optional[float]:
    """Cleans currency symbols, commas, and whitespace into a float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip()
    # Remove currency symbols and formatting commas
    cleaned = re.sub(r"[₹$,\sA-Za-z]", "", val_str)
    try:
        return float(cleaned)
    except Exception:
        return None


def parse_payment_channel(val: Any) -> PaymentChannel:
    """Standardizes channel strings into PaymentChannel enum."""
    if not val:
        return PaymentChannel.IMPS

    v = str(val).strip().upper()
    if "UPI" in v:
        return PaymentChannel.UPI
    elif "IMPS" in v:
        return PaymentChannel.IMPS
    elif "NEFT" in v:
        return PaymentChannel.NEFT
    elif "RTGS" in v:
        return PaymentChannel.RTGS
    elif "CASH" in v:
        return PaymentChannel.CASH_DEPOSIT
    elif "CHEQUE" in v or "CHECK" in v:
        return PaymentChannel.CHEQUE
    elif "ATM" in v:
        return PaymentChannel.ATM_WITHDRAWAL
    else:
        return PaymentChannel.BANK_TRANSFER


def normalize_record(raw_dict: Dict[str, Any], header_map: Dict[str, str]) -> Dict[str, Any]:
    """Converts a raw row dict into normalized canonical keys."""
    normalized: Dict[str, Any] = {}
    for orig_key, val in raw_dict.items():
        canonical_key = header_map.get(orig_key, orig_key)
        normalized[canonical_key] = val
    return normalized
