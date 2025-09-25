############################
############################
# infra/aws/live/dev/us-east-1/app/lambda.tf
############################

resource "aws_lambda_function" "api" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_exec.arn
  runtime       = var.lambda_runtime
  handler       = "app.main.handler"   # Mangum(app) exposes handler

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      TASKS_FILE    = "/tmp/tasks.json"
      # Prefer explicit value; otherwise automatically allow the CloudFront domain
      ALLOW_ORIGINS = var.allow_origins != "" ? var.allow_origins : "https://${aws_cloudfront_distribution.cdn.domain_name}"
    }
  }

  # 512MB/timeout are safe defaults; tweak as needed
  memory_size = 512
  timeout     = 10

  tags = local.tags

  # Let CI update code outside Terraform to avoid perpetual diffs
  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
    ]
  }
}
