############################
# infra/aws/live/dev/us-east-1/app/variables.tf
############################

# Project name, used in tags and resource names
variable "project" {
  type        = string
  description = "Project identifier, e.g. multicloud-devops-demo"
}

# Environment (dev, uat, prod, etc.)
variable "env" {
  type        = string
  description = "Deployment environment name"
}

# AWS region to deploy into
variable "aws_region" {
  type        = string
  description = "AWS region for resources"
  default     = "us-east-1"
}

# --- Frontend variables ---
variable "frontend_bucket_name" {
  type        = string
  description = "S3 bucket name for hosting frontend assets"
}

# --- Lambda variables ---
variable "lambda_function_name" {
  type        = string
  description = "Name of the Lambda function"
  default     = "fastapi-tasks"
}

variable "lambda_runtime" {
  type        = string
  description = "Lambda runtime version"
  default     = "python3.12"
}

variable "lambda_zip_path" {
  type        = string
  description = "Path to Lambda deployment package (.zip)"
}

variable "allow_origins" {
  type        = string
  description = "Comma-separated list of allowed origins for CORS"
  default     = "*"
}