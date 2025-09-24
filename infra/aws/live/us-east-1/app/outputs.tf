############################
# infra/aws/live/dev/us-east-1/app/outputs.tf
############################

# CloudFront domain for frontend
output "cdn_domain" {
  description = "The CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

# CloudFront distribution ID (used for invalidations)
output "cf_distribution_id" {
  description = "The CloudFront distribution ID"
  value       = aws_cloudfront_distribution.cdn.id
}

# API Gateway base URL
output "api_base_url" {
  description = "The base URL for the API Gateway"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

# Lambda ARN (for debugging / reference)
output "lambda_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.api.arn
}

# Lambda function name
output "lambda_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.api.function_name
}

# Frontend bucket name (for uploads)
output "frontend_bucket" {
  description = "S3 bucket name for the frontend"
  value       = aws_s3_bucket.site.bucket
}
