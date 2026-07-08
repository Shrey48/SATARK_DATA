"""Validates payments before processing."""
from src.payments.models import Payment, PaymentMethod


class PaymentValidator:
    def __init__(self) -> None:
        self._validated_count = 0
        self._rejected_count = 0

    def validate(self, payment: Payment) -> bool:
        if not self._check_amount(payment):
            self._reject(payment, "invalid amount")
            return False
        if not self._check_method(payment):
            self._reject(payment, "unsupported method")
            return False
        if not self._check_currency(payment):
            self._reject(payment, "unsupported currency")
            return False
        self._validated_count += 1
        return True

    def _check_amount(self, payment: Payment) -> bool:
        return payment.amount_cents > 0 and payment.amount_cents <= 10_000_000

    def _check_method(self, payment: Payment) -> bool:
        return payment.method in (
            PaymentMethod.CARD,
            PaymentMethod.WALLET,
            PaymentMethod.BANK_TRANSFER,
        )

    def _check_currency(self, payment: Payment) -> bool:
        return payment.currency in ("USD", "EUR", "GBP", "INR")

    def _reject(self, payment: Payment, reason: str) -> None:
        self._rejected_count += 1

    def stats(self) -> dict:
        return {
            "validated": self._validated_count,
            "rejected": self._rejected_count,
        }
