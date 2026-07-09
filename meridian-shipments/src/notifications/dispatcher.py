"""Dispatches shipment notifications and archives delivery-status documents."""
import json
import os

from src.common.aws_clients import get_s3_client
from src.shipments.models import Shipment
from src.notifications.templates import render_email_subject, render_status_message


class NotificationDispatcher:
    def __init__(self) -> None:
        self.s3 = get_s3_client()

    def dispatch(self, shipment: Shipment) -> None:
        message = render_status_message(shipment)
        subject = render_email_subject(shipment)
        self._send(subject, message)
        self._archive_proof_of_status(shipment, message)

    def _send(self, subject: str, message: str) -> None:
        print(f"Sending notification: {subject} -- {message}")

    def _archive_proof_of_status(self, shipment: Shipment, message: str) -> None:
        bucket_var = os.environ["SHIPMENT_DOCS_BUCKET_KEY"]
        key = f"status-events/{shipment.shipment_id}.json"
        self.s3.put_object(
            Bucket=bucket_var,
            Key=key,
            Body=json.dumps({"shipment_id": shipment.shipment_id, "message": message}),
        )
