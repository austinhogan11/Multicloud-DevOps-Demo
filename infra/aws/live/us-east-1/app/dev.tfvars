############################
# infra/aws/live/dev/us-east-1/app/dev.tfvars
############################

project              = "multicloud-devops-demo"
env                  = "dev"
aws_region           = "us-east-1"

# Frontend (globally unique bucket name)
frontend_bucket_name = "taskapi-demo-frontend-mcdd"

# Lambda
lambda_function_name = "fastapi-tasks-dev-mcdd"
lambda_runtime       = "python3.12"
lambda_zip_path      = "../../../../../build/lambda.zip"

# CORS: leave empty to auto-allow the deployed CloudFront domain
allow_origins        = ""
