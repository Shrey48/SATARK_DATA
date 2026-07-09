"""Core shipment tracking logic."""
from typing import Dict, List, Optional

from src.shipments.models import Shipment, ShipmentStatus
from src.shipments.repository import ShipmentRepository


class ShipmentTracker:
    """Coordinates shipment lifecycle transitions and persistence."""

    def __init__(self, repository: ShipmentRepository) -> None:
        self.repository = repository
        self._active_shipments: Dict[str, Shipment] = {}

    def register_shipment(self, shipment: Shipment) -> None:
        self._active_shipments[shipment.shipment_id] = shipment
        self._persist(shipment)

    def advance_status(self, shipment_id: str, new_status: ShipmentStatus) -> Optional[Shipment]:
        shipment = self._get_shipment(shipment_id)
        if shipment is None:
            return None
        shipment.mark_status(new_status)
        self._persist(shipment)
        if shipment.is_terminal():
            self._evict(shipment_id)
        return shipment

    def _get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        if shipment_id in self._active_shipments:
            return self._active_shipments[shipment_id]
        shipment = self.repository.find_by_id(shipment_id)
        if shipment:
            self._active_shipments[shipment_id] = shipment
        return shipment

    def _persist(self, shipment: Shipment) -> None:
        self.repository.save(shipment)

    def _evict(self, shipment_id: str) -> None:
        self._active_shipments.pop(shipment_id, None)

    def list_overdue(self, shipments: List[Shipment]) -> List[Shipment]:
        return [s for s in shipments if not s.is_terminal()]
