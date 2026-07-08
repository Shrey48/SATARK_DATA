"""Inventory reservation and snapshot service.

TEST PROBES:
  _decrement / _load_and_reserve — os.environ["INVENTORY_TABLE_KEY"]
      dynamodb client, env hint "INVENTORY" should heuristic-match
      Terraform aws_dynamodb_table.inventory_table (node_type: aws_dynamodb_table).
      Tests that the node_type vocabulary fix generalises to DynamoDB.

  upload_snapshot — os.environ["INVENTORY_BUCKET_KEY"]
      s3 client, env hint "INVENTORY_BUCKET" should heuristic-match
      Terraform aws_s3_bucket.inventory_snapshots (node_type: aws_s3_bucket).
      Tests that the node_type vocabulary fix generalises to S3 Terraform nodes.
"""
import os

import boto3

from src.inventory.cache import InventoryCache


class InventoryService:
    def __init__(self) -> None:
        self.cache = InventoryCache()

    def reserve(self, sku: str, quantity: int) -> bool:
        if self.cache.has(sku):
            available = self.cache.get(sku)
            if available is not None and available >= quantity:
                return self._decrement(sku, quantity)
        return self._load_and_reserve(sku, quantity)

    def release(self, sku: str, quantity: int) -> None:
        self._increment(sku, quantity)
        self.cache.invalidate(sku)

    def _decrement(self, sku: str, quantity: int) -> bool:
        dynamodb = boto3.client("dynamodb")
        table_name = os.environ["INVENTORY_TABLE_KEY"]
        dynamodb.update_item(
            TableName=table_name,
            Key={"sku": {"S": sku}},
            UpdateExpression="SET quantity = quantity - :q",
            ExpressionAttributeValues={":q": {"N": str(quantity)}},
            ConditionExpression="quantity >= :q",
        )
        self.cache.invalidate(sku)
        return True

    def _increment(self, sku: str, quantity: int) -> None:
        dynamodb = boto3.client("dynamodb")
        table_name = os.environ["INVENTORY_TABLE_KEY"]
        dynamodb.update_item(
            TableName=table_name,
            Key={"sku": {"S": sku}},
            UpdateExpression="SET quantity = quantity + :q",
            ExpressionAttributeValues={":q": {"N": str(quantity)}},
        )

    def _load_and_reserve(self, sku: str, quantity: int) -> bool:
        dynamodb = boto3.client("dynamodb")
        table_name = os.environ["INVENTORY_TABLE_KEY"]
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"sku": {"S": sku}},
        )
        item = response.get("Item")
        if not item:
            return False
        available = int(item.get("quantity", {}).get("N", "0"))
        if available < quantity:
            return False
        return self._decrement(sku, quantity)

    def upload_snapshot(self, data: bytes) -> None:
        s3 = boto3.client("s3")
        bucket_var = os.environ["INVENTORY_BUCKET_KEY"]
        s3.put_object(
            Bucket=bucket_var,
            Key="snapshots/latest.bin",
            Body=data,
        )
