"""Core payment processor.

TEST PROBES:
  _archive_payment  — self.s3.put_object(Bucket="apex-payment-artifacts-prod")
                      self-attribute boto3 pattern; regression test for self-call resolver.
                      If fixed: literal_exact_match to apex-aws-prod S3 bucket.
  _authorize        — bare-local lambda_client.invoke(FunctionName="apex-auth-checker")
                      should literal_exact_match to the apex-auth-checker Lambda in apex-aws-prod.
"""
import json

import boto3

from src.payments.models import Payment, PaymentResult, PaymentStatus
from src.payments.validator import PaymentValidator


class PaymentProcessor:
    def __init__(self) -> None:
        self.validator = PaymentValidator()
        self.s3 = boto3.client("s3")

    def process(self, payment: Payment) -> PaymentResult:
        if not self.validator.validate(payment):
            return self._build_result(False, payment.payment_id, "validation failed")
        self._archive_payment(payment)
        return self._authorize(payment)

    def refund(self, payment: Payment) -> PaymentResult:
        if not payment.is_refundable():
            return self._build_result(False, payment.payment_id, "not refundable")
        self._archive_payment(payment)
        return self._build_result(True, payment.payment_id, "refunded")

    def _authorize(self, payment: Payment) -> PaymentResult:
        lambda_client = boto3.client("lambda")
        response = lambda_client.invoke(
            FunctionName="apex-auth-checker",
            Payload=json.dumps({"payment_id": payment.payment_id}).encode(),
        )
        if response.get("StatusCode") == 200:
            return self._build_result(True, payment.payment_id, "authorized")
        return self._build_result(False, payment.payment_id, "auth failed")

    def _archive_payment(self, payment: Payment) -> None:
        self.s3.put_object(
            Bucket="apex-payment-artifacts-prod",
            Key=f"payments/{payment.payment_id}.json",
            Body=json.dumps({
                "payment_id": payment.payment_id,
                "amount": payment.amount_cents,
                "currency": payment.currency,
                "status": payment.status.value,
            }).encode(),
        )

    def _build_result(self, success: bool, payment_id: str, message: str) -> PaymentResult:
        return PaymentResult(success=success, payment_id=payment_id, message=message)
