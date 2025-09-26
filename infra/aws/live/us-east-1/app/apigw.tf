############################
# infra/aws/live/dev/us-east-1/app/apigw.tf
############################

# HTTP API (v2) — simpler/cheaper than REST API for this use case
locals {
  # Reuse the same origin logic as Lambda: explicit var or the CloudFront domain
  allowed_origin = var.allow_origins != "" ? var.allow_origins : "https://${aws_cloudfront_distribution.cdn.domain_name}"
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project}-${var.env}-http"
  protocol_type = "HTTP"

  # Let API Gateway handle CORS preflight with the same origin we allow at the app level.
  cors_configuration {
    allow_origins     = [local.allowed_origin]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["*"]
    allow_credentials = true
    max_age           = 600
  }

  tags = local.tags
}

resource "aws_apigatewayv2_integration" "lambda_proxy" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

# Single catch-all route; FastAPI does the actual routing
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_proxy.id}"
}

# Default stage with auto-deploy (no manual deploys needed)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
  tags        = local.tags
}

# Allow API Gateway to invoke the Lambda
resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowInvokeFromApiGW"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
