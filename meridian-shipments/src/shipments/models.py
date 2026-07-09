"""Domain models for shipment tracking."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ShipmentStatus(Enum):
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"


@dataclass
class Shipment:
    shipment_id: str
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.CREATED
    carrier: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def mark_status(self, status: ShipmentStatus) -> None:
        self.status = status
        self.last_updated = datetime.utcnow()

    def is_terminal(self) -> bool:
        return self.status in (ShipmentStatus.DELIVERED, ShipmentStatus.EXCEPTION)
