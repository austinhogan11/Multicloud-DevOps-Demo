#!/usr/bin/env bash
set -euo pipefail

# Builds lambda.zip (Linux), applies Terraform (using dev.tfvars),
# updates CORS to the CloudFront domain, writes frontend/.env.production,
# and prints the final URLs.

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

ARCH=${ARCH:-x86_64}             # x86_64 or arm64
PLATFORM=$([ "$ARCH" = arm64 ] && echo linux/arm64 || echo linux/amd64)

STACK_DIR="infra/aws/live/us-east-1/app"
TFVARS="$STACK_DIR/dev.tfvars"
BUILD_DIR="$ROOT_DIR/build"
PKG_DIR="$BUILD_DIR/deps"
ZIP_FILE="$BUILD_DIR/lambda.zip"

echo "[1/5] Build lambda.zip for Linux ($ARCH)"
rm -rf "$PKG_DIR" "$ZIP_FILE"
mkdir -p "$PKG_DIR"
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT_DIR":/var/task -w /var/task \
  --entrypoint /bin/sh public.ecr.aws/sam/build-python3.12:latest -lc '
    python -V && pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r app/requirements.txt -t build/deps
  '
cp -R app "$PKG_DIR"/
(cd "$PKG_DIR" && zip -qr "$ZIP_FILE" .)
echo "  -> $ZIP_FILE"

echo "[2/5] Terraform init + apply"
export TF_CLI_ARGS_apply="-auto-approve"
terraform -chdir="$STACK_DIR" init -upgrade
terraform -chdir="$STACK_DIR" apply -var-file=dev.tfvars

echo "[3/5] Capture outputs and configure frontend env"
OUT_JSON=$(terraform -chdir="$STACK_DIR" output -json)

# Fallback to Python json parsing if jq is missing
have_jq=1
command -v jq >/dev/null 2>&1 || have_jq=0
if [ "$have_jq" -eq 1 ]; then
  CDN_DOMAIN=$(echo "$OUT_JSON" | jq -r .cdn_domain.value)
  API_BASE_URL=$(echo "$OUT_JSON" | jq -r .api_base_url.value)
  CF_DIST_ID=$(echo "$OUT_JSON" | jq -r .cf_distribution_id.value)
else
  CDN_DOMAIN=$(python - <<'PY'
import json,sys
d=json.load(sys.stdin)
print(d['cdn_domain']['value'])
PY
<<<"$OUT_JSON")
  API_BASE_URL=$(python - <<'PY'
import json,sys
d=json.load(sys.stdin)
print(d['api_base_url']['value'])
PY
<<<"$OUT_JSON")
  CF_DIST_ID=$(python - <<'PY'
import json,sys
d=json.load(sys.stdin)
print(d['cf_distribution_id']['value'])
PY
<<<"$OUT_JSON")
fi

# Write frontend/.env.production
ENV_FILE="$ROOT_DIR/frontend/.env.production"
echo "VITE_API_BASE=$API_BASE_URL" > "$ENV_FILE"
echo "  -> wrote $ENV_FILE"

echo "[4/5] Ensure CORS allows the CDN origin and re-apply if needed"
ALLOW_ORIGINS_LINE="allow_origins        = \"https://$CDN_DOMAIN\""
if grep -q '^allow_origins\s*=' "$TFVARS"; then
  if ! grep -q "$CDN_DOMAIN" "$TFVARS"; then
    # replace existing allow_origins line
    tmp="$TFVARS.tmp" && awk -v repl="$ALLOW_ORIGINS_LINE" '
      BEGIN{done=0}
      /^allow_origins\s*=/{print repl; done=1; next}
      {print}
      END{if(!done) print repl}
    ' "$TFVARS" > "$tmp" && mv "$tmp" "$TFVARS"
    echo "  -> updated CORS in $TFVARS to https://$CDN_DOMAIN"
    terraform -chdir="$STACK_DIR" apply -var-file=dev.tfvars
  else
    echo "  -> CORS already allows https://$CDN_DOMAIN"
  fi
else
  echo "$ALLOW_ORIGINS_LINE" >> "$TFVARS"
  echo "  -> added CORS to $TFVARS"
  terraform -chdir="$STACK_DIR" apply -var-file=dev.tfvars
fi

echo "[5/5] Summary"
cat <<EOF

Frontend (CloudFront):  https://$CDN_DOMAIN
API (API Gateway):      $API_BASE_URL
CF Distribution ID:     $CF_DIST_ID

Next:
  1) Build frontend and upload to S3:
       cd frontend && npm ci && npm run build
       aws s3 sync dist/ s3://$(terraform -chdir="$STACK_DIR" output -raw frontend_bucket || echo "<your-bucket>") --delete || true
  2) Invalidate CloudFront:
       aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"
EOF

