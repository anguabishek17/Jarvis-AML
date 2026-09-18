"""
Robust Multi-Point Validation Engine for Custom Transaction Ingestion.
Parses CSV text/file or JSON objects, executes integrity checks, and generates a structured ValidationReport.
"""
import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from backend.models.transaction import Transaction, PaymentChannel, TransactionType, TransactionStatus
from backend.ingestion.normalizer import (
    map_column_headers,
    parse_flexible_timestamp,
    parse_flexible_amount,
    parse_payment_channel,
    normalize_record,
)


class ValidationReport(BaseModel):
    total_rows: int = Field(default=0)
    valid_rows: int = Field(default=0)
    invalid_rows: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    detected_headers: List[str] = Field(default_factory=list)
    mapped_headers: Dict[str, str] = Field(default_factory=dict)
    is_acceptable_for_analysis: bool = Field(default=False)
    unique_accounts_count: int = Field(default=0)
    total_volume_inr: float = Field(default=0.0)


class TransactionValidator:
    """Validates raw transaction records from CSV or JSON sources."""

    def validate_csv_text(self, csv_content: str, max_rows: int = 50000) -> Tuple[ValidationReport, List[Transaction]]:
        if not csv_content or not csv_content.strip():
            report = ValidationReport(
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=["The submitted CSV dataset is empty."],
                is_acceptable_for_analysis=False,
            )
            return report, []

        try:
            reader = csv.DictReader(io.StringIO(csv_content.strip()))
            raw_headers = reader.fieldnames or []
        except Exception as e:
            return ValidationReport(
                errors=[f"Failed to parse CSV format: {str(e)}"],
                is_acceptable_for_analysis=False,
            ), []

        if not raw_headers:
            return ValidationReport(
                errors=["Unable to detect CSV header row. Ensure the first line contains column names."],
                is_acceptable_for_analysis=False,
            ), []

        raw_rows = []
        for idx, row in enumerate(reader):
            if idx >= max_rows:
                break
            raw_rows.append(row)

        return self.validate_dict_records(raw_rows, raw_headers)

    def validate_dict_records(self, raw_rows: List[Dict[str, Any]], raw_headers: List[str]) -> Tuple[ValidationReport, List[Transaction]]:
        header_map, missing_required = map_column_headers(raw_headers)

        report = ValidationReport(
            total_rows=len(raw_rows),
            detected_headers=raw_headers,
            mapped_headers=header_map,
        )

        if missing_required:
            report.errors.append(
                f"Missing required column(s): {', '.join(missing_required)}. "
                f"Expected aliases for: transaction_id, sender, receiver, amount, timestamp."
            )
            report.is_acceptable_for_analysis = False
            return report, []

        valid_txs: List[Transaction] = []
        seen_tx_ids = set()
        unique_accounts = set()
        total_vol = 0.0

        for row_idx, raw_row in enumerate(raw_rows, start=1):
            norm = normalize_record(raw_row, header_map)

            # 1. Transaction ID
            tx_id_raw = norm.get("transaction_id")
            if not tx_id_raw or str(tx_id_raw).strip() == "":
                tx_id = f"TXN_AUTO_{row_idx:05d}"
                report.warnings.append(f"Row {row_idx}: Missing transaction_id. Auto-assigned '{tx_id}'.")
            else:
                tx_id = str(tx_id_raw).strip()

            if tx_id in seen_tx_ids:
                report.warnings.append(f"Row {row_idx}: Duplicate transaction ID '{tx_id}'. Deduplicating with suffix.")
                tx_id = f"{tx_id}_DUP_{row_idx}"
            seen_tx_ids.add(tx_id)

            # 2. Sender and Receiver
            sender_raw = norm.get("sender") or norm.get("sender_account") or norm.get("source")
            receiver_raw = norm.get("receiver") or norm.get("receiver_account") or norm.get("destination")

            if not sender_raw or str(sender_raw).strip() == "":
                report.invalid_rows += 1
                report.errors.append(f"Row {row_idx}: Empty or missing sender account.")
                continue

            if not receiver_raw or str(receiver_raw).strip() == "":
                report.invalid_rows += 1
                report.errors.append(f"Row {row_idx}: Empty or missing receiver account.")
                continue

            sender = str(sender_raw).strip()
            receiver = str(receiver_raw).strip()

            if sender == receiver:
                report.warnings.append(f"Row {row_idx}: Self-transfer detected ({sender} → {receiver}).")

            # 3. Amount
            amount_val = parse_flexible_amount(norm.get("amount"))
            if amount_val is None or amount_val <= 0:
                report.invalid_rows += 1
                report.errors.append(f"Row {row_idx}: Invalid or non-positive amount '{norm.get('amount')}'.")
                continue

            # 4. Timestamp
            dt_val = parse_flexible_timestamp(norm.get("timestamp"))
            if dt_val is None:
                report.invalid_rows += 1
                report.errors.append(f"Row {row_idx}: Invalid timestamp format '{norm.get('timestamp')}'.")
                continue

            # 5. Optional fields
            channel_enum = parse_payment_channel(norm.get("channel"))
            currency_str = str(norm.get("currency") or "INR").strip().upper()
            remarks_str = str(norm.get("remarks") or norm.get("description") or "").strip()

            try:
                tx = Transaction(
                    transaction_id=tx_id,
                    timestamp=dt_val,
                    sender_account=sender,
                    receiver_account=receiver,
                    amount=amount_val,
                    currency=currency_str,
                    channel=channel_enum,
                    transaction_type=TransactionType.TRANSFER,
                    status=TransactionStatus.COMPLETED,
                    remarks=remarks_str,
                    metadata={"source_row": row_idx},
                )
                valid_txs.append(tx)
                report.valid_rows += 1
                unique_accounts.add(sender)
                unique_accounts.add(receiver)
                total_vol += amount_val
            except Exception as ex:
                report.invalid_rows += 1
                report.errors.append(f"Row {row_idx}: Model instantiation error: {str(ex)}")

        report.unique_accounts_count = len(unique_accounts)
        report.total_volume_inr = round(total_vol, 2)
        report.is_acceptable_for_analysis = report.valid_rows > 0

        return report, valid_txs
