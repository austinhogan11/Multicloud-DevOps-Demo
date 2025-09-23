#!/usr/bin/env bash
set -euo pipefail

# Build a Lambda-ready zip (Linux wheels) into lambda.zip
# Requirements are installed from app/requirements.txt

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PKG_DIR="lambda_pkg"
ZIP_FILE="lambda.zip"

# Architecture for Lambda: x86_64 or arm64
# Set ARCH=arm64 to build for Graviton functions
ARCH=${ARCH:-x86_64}
case "$ARCH" in
  x86_64) PLATFORM="linux/amd64" ;;
  arm64)  PLATFORM="linux/arm64" ;;
  *) echo "Unknown ARCH='$ARCH' (use x86_64 or arm64)"; exit 1 ;;
esac

echo "[1/4] Cleaning output..."
rm -rf "$PKG_DIR" "$ZIP_FILE"
mkdir -p "$PKG_DIR"

echo "[2/4] Installing deps into $PKG_DIR (Python 3.12, $ARCH)..."
docker run --rm --platform "$PLATFORM" \
  -v "$PWD":/var/task \
  -w /var/task \
  --entrypoint /bin/sh \
  public.ecr.aws/sam/build-python3.12:latest \
  -c "python -V && pip install --upgrade pip && pip install -r app/requirements.txt -t '$PKG_DIR' && python -c 'import platform; print(platform.platform())'"

echo "[3/4] Adding application code..."
mkdir -p "$PKG_DIR/app"
rsync -a app/ "$PKG_DIR/app/" \
  --exclude "__pycache__" --exclude "*.pyc" --exclude "*.pyo"

echo "[4/4] Creating zip: $ZIP_FILE"
(cd "$PKG_DIR" && zip -qr "../$ZIP_FILE" .)

# Minimal verification
if ! ls -1 $PKG_DIR/pydantic_core/_pydantic_core*.so > /dev/null 2>&1; then
  echo "WARNING: pydantic_core native module not found in $PKG_DIR."
  echo "If your Lambda is arm64, run: ARCH=arm64 bash scripts/build_lambda.sh"
fi

echo "Done. Upload $ZIP_FILE to Lambda."
echo "Runtime: Python 3.12 | Handler: app.main.handler"
echo "Optional env for temp persistence: TASKS_FILE=/tmp/tasks.json"
