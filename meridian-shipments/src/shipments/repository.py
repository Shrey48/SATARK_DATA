"""DynamoDB-backed persistence for shipments."""
from typing import Optional

from src.common.aws_clients import get_dynamodb_client
from src.shipments.models import Shipment, ShipmentStatus

TABLE_NAME = "meridian-shipments"


class ShipmentRepository:
    def __init__(self) -> None:
        self.table = get_dynamodb_client()

    def save(self, shipment: Shipment) -> None:
        self.table.put_item(
            TableName=TABLE_NAME,
            Item={
                "shipment_id": {"S": shipment.shipment_id},
                "status": {"S": shipment.status.value},
                "origin": {"S": shipment.origin},
                "destination": {"S": shipment.destination},
            },
        )

    def find_by_id(self, shipment_id: str) -> Optional[Shipment]:
        response = self.table.get_item(
            TableName=TABLE_NAME,
            Key={"shipment_id": {"S": shipment_id}},
        )
        item = response.get("Item")
        if not item:
            return None
        return Shipment(
            shipment_id=item["shipment_id"]["S"],
            origin=item["origin"]["S"],
            destination=item["destination"]["S"],
            status=ShipmentStatus(item["status"]["S"]),
        )

    def delete(self, shipment_id: str) -> None:
        self.table.delete_item(
            TableName=TABLE_NAME,
            Key={"shipment_id": {"S": shipment_id}},
        )
