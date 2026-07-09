resource "aws_iam_role" "shipment_lambda_role" {
  name = "meridian-shipment-lambda-role"

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

resource "aws_lambda_function" "shipment_processor" {
  function_name = "shipment-processor"
  role          = aws_iam_role.shipment_lambda_role.arn
  handler       = "src.shipments.tracker.handler"
  runtime       = "python3.11"
  filename      = "build/shipment_processor.zip"
}

resource "aws_dynamodb_table" "shipments_table" {
  name         = "meridian-shipments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "shipment_id"

  attribute {
    name = "shipment_id"
    type = "S"
  }
}

resource "aws_iam_role" "notification_lambda_role" {
  name = "meridian-notification-lambda-role"

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

resource "aws_lambda_function" "notification_dispatcher" {
  function_name = "notification-dispatcher"
  role          = aws_iam_role.notification_lambda_role.arn
  handler       = "src.notifications.dispatcher.handler"
  runtime       = "python3.11"
  filename      = "build/notification_dispatcher.zip"
}

# Deliberately references a role that is not defined anywhere in this asset,
# so within-asset Terraform resolution should leave this edge as an honest stub.
resource "aws_lambda_function" "shipment_archiver" {
  function_name = "shipment-archiver"
  role          = aws_iam_role.legacy_unmanaged_role.arn
  handler       = "src.common.aws_clients.invoke_archiver"
  runtime       = "python3.11"
  filename      = "build/shipment_archiver.zip"
}
