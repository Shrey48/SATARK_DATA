"""Thin wrappers around boto3 clients used across the service."""
import boto3

_DEFAULT_REGION = "us-east-1"


def get_s3_client():
    return boto3.client("s3", region_name=_DEFAULT_REGION)


def get_dynamodb_client():
    return boto3.client("dynamodb", region_name=_DEFAULT_REGION)


def get_lambda_client():
    return boto3.client("lambda", region_name=_DEFAULT_REGION)


def invoke_archiver(payload: bytes) -> dict:
    lambda_client = get_lambda_client()
    return lambda_client.invoke(
        FunctionName="shipment-archiver",
        Payload=payload,
    )
