

# AWS Deployment Steps

This project deploys a React frontend and a FastAPI backend.
- Frontend → **S3 + CloudFront**
- Backend → **Lambda + API Gateway (HTTP API)**

---

## 1) Backend Deployment (FastAPI → Lambda + API Gateway)

### A. Prepare locally
1. Ensure the Lambda adapter exists in `app/main.py`:
   ```python
   # Optional AWS Lambda handler (active in Lambda or when ENABLE_MANGUM=1)
   try:
       from mangum import Mangum  # type: ignore
       _has_mangum = True
   except Exception:
       _has_mangum = False

   if _has_mangum and (os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("ENABLE_MANGUM") == "1"):
       handler = Mangum(app)
   ```
2. Dependencies for Lambda package:
   ```bash
   # from repo root or backend env
   pip install fastapi mangum uvicorn pydantic
   pip freeze | grep -E 'fastapi|mangum|uvicorn|pydantic' >> app/requirements.txt
   ```
3. Build the Lambda zip:
   ```bash
   rm -rf lambda_pkg lambda.zip
   mkdir -p lambda_pkg
   pip install --target lambda_pkg -r app/requirements.txt
   cp -r app lambda_pkg/
   (cd lambda_pkg && zip -r ../lambda.zip .)
   ```

### B. Create IAM role (console)
1. AWS Console → **IAM → Roles → Create role**
2. Trusted entity: **Lambda**
3. Attach policy: **AWSLambdaBasicExecutionRole**
4. Name: `role-fastapi-lambda`

### C. Create Lambda function (console)
1. AWS Console → **Lambda → Create function → Author from scratch**
2. Name: `fastapi-tasks`, Runtime: **Python 3.11**, Role: `role-fastapi-lambda`
3. Upload `lambda.zip` (Code → Upload from → .zip)
4. **Handler**: `app.main.handler`
5. **Environment variables** (recommended):
   - `TASKS_FILE=/tmp/tasks.json`  (Lambda writes only to `/tmp`)
   - `ALLOWED_ORIGINS=https://<your-cloudfront-domain>,http://localhost:5173`

### D. Create API Gateway (HTTP API)
1. AWS Console → **API Gateway → Create API → HTTP API**
2. Integration: your Lambda `fastapi-tasks`
3. Route: `$default` (or `ANY /{proxy+}`) → Lambda
4. CORS: enable (temporarily `*`, later restrict to CloudFront domain)
5. Deploy and copy the **Invoke URL**

### E. Smoke test
```bash
curl https://<invoke-id>.execute-api.<region>.amazonaws.com/health
# expect: {"status":"ok"}
```

---

## 2) Frontend Deployment (React → S3 + CloudFront)

### A. Build with API URL
```bash
cd frontend
# .env used by Vite at build time
printf "VITE_API_URL=https://<invoke-id>.execute-api.<region>.amazonaws.com\n" > .env
npm run build
```

### B. Create S3 bucket
1. S3 → **Create bucket** (e.g., `carters-demo-frontend-<unique>`)
2. Keep **Block all public access = ON** (we will use CloudFront OAC)

### C. Upload build to S3
```bash
aws s3 sync ./dist s3://carters-demo-frontend-<unique> --delete
```

### D. Create CloudFront distribution
1. Origin: the S3 bucket with **Origin Access Control (OAC)**
2. Default root object: `index.html`
3. Custom error responses (SPA fallback):
   - 403 → Respond with **200**, **/index.html**
   - 404 → Respond with **200**, **/index.html**
4. (Optional) Custom domain: create ACM cert in **us-east-1**, add CNAME, update DNS
5. Copy the CloudFront **Domain Name** (e.g., `dxxxx.cloudfront.net`)

### E. Restrict CORS to CloudFront domain
- Update Lambda env `ALLOWED_ORIGINS` to your CloudFront URL
- Remove `*` in API Gateway CORS once testing is complete

### F. Test
- Open the CloudFront URL and verify the UI loads and calls the API

---

## 3) Update Cycles

### Backend (Lambda)
```bash
rm -rf lambda_pkg lambda.zip && mkdir -p lambda_pkg
pip install --target lambda_pkg -r app/requirements.txt
cp -r app lambda_pkg/
(cd lambda_pkg && zip -r ../lambda.zip .)
aws lambda update-function-code --function-name fastapi-tasks --zip-file fileb://lambda.zip
```

### Frontend (S3 + CloudFront)
```bash
cd frontend && npm run build
aws s3 sync dist/ s3://carters-demo-frontend-<unique> --delete
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```

---

## 4) Notes & Tips
- **CORS**: use `ALLOWED_ORIGINS` env to list allowed origins (comma-separated). Lock to your CloudFront domain in prod.
- **Lambda filesystem**: only `/tmp` is writable. Use `TASKS_FILE=/tmp/tasks.json` for JSON persistence.
- **Costs**: Lambda + API Gateway + S3 + CloudFront usually stay in free tier for low traffic. Keep your $5/month budget and free-tier alerts enabled.
- **Tear down**: remove distributions and buckets when not in use to avoid charges.