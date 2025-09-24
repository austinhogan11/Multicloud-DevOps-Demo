#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Terraform remote state on AWS (S3 bucket + DynamoDB lock table).
# Idempotent: will reuse existing resources if present.

REGION=${REGION:-us-east-1}
BUCKET=${BUCKET:-multicloud-devops-demo-tfstate}
TABLE=${TABLE:-multicloud-devops-demo-tflock}

echo "Region     : $REGION"
echo "State bucket: $BUCKET"
echo "Lock table : $TABLE"

# Disable AWS CLI pager so the script never pauses with a (END) screen
export AWS_PAGER=""

aws --no-cli-pager --region "$REGION" s3api head-bucket --bucket "$BUCKET" 2>/dev/null || {
  echo "Creating S3 bucket s3://$BUCKET ..."
  if [ "$REGION" = "us-east-1" ]; then
    aws --no-cli-pager s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws --no-cli-pager s3api create-bucket --bucket "$BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
  fi
}

echo "Enabling versioning on s3://$BUCKET ..."
aws --no-cli-pager --region "$REGION" s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled

echo "Creating/ensuring DynamoDB table $TABLE ..."
aws --no-cli-pager --region "$REGION" dynamodb describe-table --table-name "$TABLE" >/dev/null 2>&1 || \
  aws --no-cli-pager --region "$REGION" dynamodb create-table \
    --table-name "$TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

cat <<EOF

Done. Configure Terraform backend with:

terraform init \
  -backend-config="bucket=$BUCKET" \
  -backend-config="key=multicloud-devops-demo/app/terraform.tfstate" \
  -backend-config="region=$REGION" \
  -backend-config="dynamodb_table=$TABLE"

GitHub repo variables to enable backend in CI:
  TF_STATE_BUCKET=$BUCKET
  TF_STATE_KEY=multicloud-devops-demo/app/terraform.tfstate
  TF_LOCK_TABLE=$TABLE
EOF
