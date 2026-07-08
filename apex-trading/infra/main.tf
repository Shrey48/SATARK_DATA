resource "aws_iam_role" "trading_admin_role" {
  name = "apex-trading-admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# NOTE: AdministratorAccess intentionally attached — legacy provisioning role
# This will trigger D2 trust escalation for findings anchored to this Lambda
resource "aws_lambda_function" "trading_processor" {
  function_name = "apex-trading-processor"
  role          = aws_iam_role.trading_admin_role.arn
  handler       = "src.trading.api.handler"
  runtime       = "python3.11"
  filename      = "build/trading_processor.zip"
}

resource "aws_iam_role" "trading_readonly_role" {
  name = "apex-trading-readonly-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_lambda_function" "fraud_scorer" {
  function_name = "apex-fraud-scorer"
  role          = aws_iam_role.trading_readonly_role.arn
  handler       = "src.trading.analytics.handler"
  runtime       = "python3.11"
  filename      = "build/fraud_scorer.zip"
}

resource "aws_dynamodb_table" "transactions" {
  name         = "apex-transactions-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  server_side_encryption { enabled = true }
}

resource "aws_s3_bucket" "trading_reports" {
  bucket = "apex-trading-reports-prod"
}
