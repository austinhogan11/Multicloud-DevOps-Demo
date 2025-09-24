############################
# infra/aws/live/dev/us-east-1/app/s3.tf
############################

# Frontend asset bucket (private; CloudFront OAC will read it)
resource "aws_s3_bucket" "site" {
  bucket = var.frontend_bucket_name
  tags   = local.tags
}

# Ensures objects are owned by the bucket owner (helps with CI/CD uploads)
resource "aws_s3_bucket_ownership_controls" "site" {
  bucket = aws_s3_bucket.site.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# Block any form of public access (CDN will access via OAC + bucket policy)
resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Optional but recommended: enable versioning (rollback protection)
resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Optional: default encryption at rest (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}