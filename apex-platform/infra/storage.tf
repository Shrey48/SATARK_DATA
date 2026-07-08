resource "aws_dynamodb_table" "payments_table" {
  name         = "apex-payments-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "payment_id"

  attribute {
    name = "payment_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "inventory_table" {
  name         = "apex-inventory-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sku"

  attribute {
    name = "sku"
    type = "S"
  }
}

resource "aws_dynamodb_table" "auth_audit_table" {
  name         = "apex-auth-audit-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

resource "aws_s3_bucket" "inventory_snapshots" {
  bucket = "apex-inventory-snapshots-prod"
}

resource "aws_s3_bucket" "reports" {
  bucket = "apex-reports-prod"
}
