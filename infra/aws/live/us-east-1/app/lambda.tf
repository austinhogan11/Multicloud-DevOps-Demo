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
      # Splunk HEC configuration (optional)
      SPLUNK_HEC_URL        = var.splunk_hec_url
      SPLUNK_HEC_TOKEN      = var.splunk_hec_token
      SPLUNK_HEC_SECRET_ARN = var.splunk_hec_secret_arn
      SPLUNK_HEC_SECRET_NAME= var.splunk_hec_secret_name
      SPLUNK_INDEX      = var.splunk_index
      SPLUNK_SOURCE     = var.splunk_source
      SPLUNK_SOURCETYPE = var.splunk_sourcetype
      SPLUNK_ENABLE     = var.splunk_enable
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
data "aws_caller_identity" "current" {}

locals {
  splunk_secret_arn = var.splunk_hec_secret_arn != "" ? var.splunk_hec_secret_arn : (var.splunk_hec_secret_name != "" ? "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.splunk_hec_secret_name}*" : "")
}

data "aws_iam_policy_document" "lambda_secrets_access" {
  count = local.splunk_secret_arn != "" ? 1 : 0
  statement {
    sid     = "SecretsRead"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [local.splunk_secret_arn]
  }
}

resource "aws_iam_policy" "lambda_secrets_access" {
  count  = local.splunk_secret_arn != "" ? 1 : 0
  name   = "${var.project}-${var.env}-lambda-secrets-access"
  policy = data.aws_iam_policy_document.lambda_secrets_access[0].json
}

resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  count      = local.splunk_secret_arn != "" ? 1 : 0
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_secrets_access[0].arn
}
