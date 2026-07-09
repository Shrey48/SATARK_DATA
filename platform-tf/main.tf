resource "aws_iam_role" "order_admin_role" {
  name = "meridian-order-admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "order_admin_attach" {
  role       = aws_iam_role.order_admin_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_lambda_function" "order_processor" {
  function_name = "meridian-order-processor"
  role          = aws_iam_role.order_admin_role.arn
  handler       = "app.submit_order"
  runtime       = "python3.11"
  filename      = "build/order_processor.zip"
  timeout       = 15
}

resource "aws_lambda_function" "compliance_processor" {
  function_name = "meridian-compliance-processor"
  role          = aws_iam_role.order_admin_role.arn
  handler       = "com.meridian.ComplianceHandler"
  runtime       = "java11"
  filename      = "build/compliance.jar"
  timeout       = 60
}

resource "aws_security_group" "api_sg_permissive" {
  name        = "meridian-api-sg"
  description = "Public API — HTTPS only"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "bastion_sg" {
  name        = "meridian-bastion-sg"
  description = "Bastion host — SSH"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # open to world — sensitive finding
  }
}

resource "aws_wafv2_web_acl" "api_waf" {
  name  = "meridian-api-waf"
  scope = "REGIONAL"

  default_action { allow {} }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "meridian-api-waf"
    sampled_requests_enabled   = true
  }
}

resource "aws_s3_bucket" "audit_logs" {
  bucket = "meridian-audit-logs-prod"
}

resource "aws_s3_bucket" "compliance_reports" {
  bucket = "meridian-compliance-reports-prod"
}

resource "aws_dynamodb_table" "orders" {
  name         = "meridian-orders-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute { name = "order_id"; type = "S" }
  server_side_encryption { enabled = true }
}

resource "aws_dynamodb_table" "market_feeds" {
  name         = "meridian-market-feeds"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"

  attribute { name = "symbol"; type = "S" }
}

variable "vpc_id" {
  type    = string
  default = "vpc-0a1b2c3d4e5f"
}
