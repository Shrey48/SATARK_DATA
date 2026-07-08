"""Auth middleware: token verification and audit logging.

TEST PROBE:
  log_auth_event — os.environ["AUTH_AUDIT_TABLE_KEY"]
      dynamodb client, env hint tokens "AUTH" + "AUDIT" should cleanly
      heuristic-match Terraform aws_dynamodb_table.auth_audit_table over
      the payments_table and inventory_table decoys.
"""
import os

import boto3

from src.payments.models import PaymentStatus


class AuthMiddleware:
    def __init__(self) -> None:
        self._sessions: dict = {}

    def verify_token(self, token: str) -> bool:
        if token in self._sessions:
            return self._check_session(token)
        return self._validate_remote(token)

    def invalidate_token(self, token: str) -> None:
        self._evict_session(token)

    def log_auth_event(self, user_id: str, success: bool) -> None:
        dynamodb = boto3.client("dynamodb")
        table_name = os.environ["AUTH_AUDIT_TABLE_KEY"]
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "user_id": {"S": user_id},
                "success": {"BOOL": success},
            },
        )

    def _check_session(self, token: str) -> bool:
        session = self._sessions.get(token)
        return session is not None and session.get("valid", False)

    def _validate_remote(self, token: str) -> bool:
        if len(token) < 16:
            return False
        self._sessions[token] = {"valid": True}
        return True

    def _evict_session(self, token: str) -> None:
        self._sessions.pop(token, None)
