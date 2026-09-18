"""
Transaction and Account data models with Indian financial context support.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PaymentChannel(str, Enum):
    UPI = "UPI"
    IMPS = "IMPS"
    NEFT = "NEFT"
    RTGS = "RTGS"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CHEQUE = "CHEQUE"
    ATM_WITHDRAWAL = "ATM_WITHDRAWAL"


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SETTLEMENT = "SETTLEMENT"


class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FLAGGED = "FLAGGED"
    REVERSED = "REVERSED"


class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: str = Field(..., description="Unique transaction reference (e.g. TXN_IN_892104)")
    timestamp: datetime = Field(..., description="ISO timestamp of transaction")
    sender_account: str = Field(..., description="Source account identifier (e.g. ACC_ORIGINATOR_A)")
    receiver_account: str = Field(..., description="Destination account identifier (e.g. ACC_GATEKEEPER_MULE)")
    amount: float = Field(..., gt=0, description="Amount in specified currency (INR)")
    currency: str = Field(default="INR", description="Currency ISO code, default INR")
    channel: PaymentChannel = Field(default=PaymentChannel.IMPS, description="Payment channel (UPI, IMPS, etc.)")
    transaction_type: TransactionType = Field(default=TransactionType.TRANSFER, description="Transaction type")
    status: TransactionStatus = Field(default=TransactionStatus.COMPLETED, description="Transaction status")
    remarks: Optional[str] = Field(default=None, description="Transaction remarks/narration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual metadata")


class Account(BaseModel):
    account_id: str = Field(..., description="Unique account identifier")
    account_holder_name: Optional[str] = Field(default=None, description="Masked/Synthetic entity name")
    account_type: Optional[str] = Field(default="SAVINGS", description="SAVINGS, CURRENT, ESCROW, CORPORATE")
    bank_name: Optional[str] = Field(default="HDFC Bank", description="Synthetic bank name")
    ifsc_code: Optional[str] = Field(default="HDFC0001234", description="Synthetic IFSC code")
    kyc_status: Optional[str] = Field(default="VERIFIED", description="KYC status")
    created_date: Optional[str] = Field(default=None, description="Account creation date")


class ScenarioMetadata(BaseModel):
    scenario_id: str = Field(..., description="Scenario identifier (e.g. SCENARIO_G)")
    title: str = Field(..., description="Scenario title")
    description: str = Field(..., description="Brief scenario synopsis")
    total_volume_inr: float = Field(default=0.0, description="Total INR volume involved")
    account_count: int = Field(default=0, description="Number of unique accounts")
    transaction_count: int = Field(default=0, description="Number of transactions")
    primary_typology: str = Field(default="", description="Primary money laundering typology")
    difficulty: str = Field(default="MEDIUM", description="Investigation complexity rating")
