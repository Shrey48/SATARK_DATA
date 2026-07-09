"""Notification message templates."""
from src.shipments.models import Shipment, ShipmentStatus

_STATUS_COPY = {
    ShipmentStatus.CREATED: "Your shipment has been created.",
    ShipmentStatus.IN_TRANSIT: "Your shipment is in transit.",
    ShipmentStatus.OUT_FOR_DELIVERY: "Your shipment is out for delivery.",
    ShipmentStatus.DELIVERED: "Your shipment has been delivered.",
    ShipmentStatus.EXCEPTION: "There is an issue with your shipment.",
}


def render_status_message(shipment: Shipment) -> str:
    body = _STATUS_COPY.get(shipment.status, "Shipment status updated.")
    return f"[{shipment.shipment_id}] {body}"


def render_email_subject(shipment: Shipment) -> str:
    return f"Update on shipment {shipment.shipment_id}"
