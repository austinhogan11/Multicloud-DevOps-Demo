############################
# infra/aws/live/dev/us-east-1/app/main.tf
############################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Remote state (S3 backend). Values are supplied via `terraform init -backend-config=...`.
  backend "s3" {}
}

# The AWS provider: tells Terraform which cloud/region/account to talk to.
provider "aws" {
  region = var.aws_region
}

# Common tags you want on every resource in this stack.
locals {
  tags = {
    Project = var.project
    Env     = var.env
    Stack   = "app"
  }
}
