resource "aws_iam_role" "payments_lambda_role" {
  name = "apex-payments-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_lambda_function" "payments_processor" {
  function_name = "apex-payments-processor"
  role          = aws_iam_role.payments_lambda_role.arn
  handler       = "src.payments.processor.handler"
  runtime       = "python3.11"
  filename      = "build/payments.zip"
}

resource "aws_iam_role" "inventory_lambda_role" {
  name = "apex-inventory-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_lambda_function" "inventory_processor" {
  function_name = "apex-inventory-processor"
  role          = aws_iam_role.inventory_lambda_role.arn
  handler       = "src.inventory.service.handler"
  runtime       = "python3.11"
  filename      = "build/inventory.zip"
}

resource "aws_iam_role" "auth_lambda_role" {
  name = "apex-auth-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_lambda_function" "auth_checker" {
  function_name = "apex-auth-checker"
  role          = aws_iam_role.auth_lambda_role.arn
  handler       = "src.auth.middleware.handler"
  runtime       = "python3.11"
  filename      = "build/auth.zip"
}

# Deliberately references a role not defined anywhere in this asset --
# should surface as an honest unresolved_terraform_reference stub.
resource "aws_lambda_function" "legacy_data_migrator" {
  function_name = "apex-legacy-data-migrator"
  role          = aws_iam_role.legacy_external_role.arn
  handler       = "legacy.migrator.run"
  runtime       = "python3.9"
  filename      = "build/legacy.zip"
}
