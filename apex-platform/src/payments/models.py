"""Domain models for payment processing."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(Enum):
    CARD = "card"
    WALLET = "wallet"
    BANK_TRANSFER = "bank_transfer"


@dataclass
class Payment:
    payment_id: str
    order_id: str
    amount_cents: int
    currency: str
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_terminal(self) -> bool:
        return self.status in (
            PaymentStatus.CAPTURED,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
        )

    def is_refundable(self) -> bool:
        return self.status == PaymentStatus.CAPTURED


@dataclass
class PaymentResult:
    success: bool
    payment_id: str
    message: str
    transaction_ref: Optional[str] = None
