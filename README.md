# Multicloud DevOps Demo

Simple Todo app to show a full stack:

- Backend: FastAPI Tasks API
- Frontend: React + Vite + Tailwind
- Persistence: JSON file (survives restarts)
- Docker: Frontend (Nginx) + Backend (Uvicorn) with Compose

## Preview

<img src="docs/todo-app.png" alt="Todo App UI" />

## Architecture

The app is a small full‑stack deployed to AWS with Terraform and GitHub Actions.

```mermaid
flowchart LR
  user([User Browser])

  subgraph FE[Frontend]
    cf[CloudFront CDN]
    s3[S3 Static Site Bucket]
  end

  subgraph BE[Backend]
    apigw[API Gateway (HTTP API)]
    lambda[(AWS Lambda\nFastAPI Task API)]
    logs[CloudWatch Logs]
  end

  subgraph CICD[CI/CD - GitHub Actions]
    gha[Actions Workflows\n(deploy-stack.yml)]
    oidc[OIDC AssumeRole]
    buildL[Build lambda.zip\n(SAM build image)]
    buildFE[Build React/Tailwind\n(Vite)]
    tf[Terraform init/apply]
    sync[S3 Sync + CF Invalidate]
  end

  subgraph TF[Terraform on AWS]
    tfs3[(S3 TF State Bucket)]
    tfdyn[(DynamoDB Lock Table)]
    res[Infra Resources\n(S3, CloudFront, API GW, Lambda, IAM)]
  end

  %% Frontend path
  user --> cf --> s3
  %% Frontend calls API
  user -. fetch tasks .-> apigw

  %% Backend path
  apigw --> lambda --> logs

  %% CI/CD wiring
  gha --> oidc -->|sts:AssumeRoleWithWebIdentity| res
  gha --> buildL --> tf
  gha --> buildFE --> sync
  tf -->|backend| tfs3
  tf -->|lock| tfdyn
  tf --> res
  res --> cf
  res --> s3
  res --> apigw
  res --> lambda

  %% Notes
  classDef note fill:#f7f7f7,stroke:#bbb,stroke-width:1px,color:#333;
  note1[[VITE_API_BASE set from TF output]]
  note2[[Lambda CORS ALLOW_ORIGINS auto-set to CloudFront domain]]
  buildFE --- note1
  lambda --- note2
```

ASCII fallback

```
User → CloudFront → S3 (static SPA)
SPA → fetch → API Gateway (HTTP) → Lambda (FastAPI)
Lambda logs → CloudWatch
GitHub Actions → (OIDC assume role) → Terraform (S3 state + DDB lock) → AWS
CI builds lambda.zip + frontend, applies TF, syncs S3, invalidates CF.
```

## What We Built

- Todo UI
  - Centered card with list, add item, edit (pen), delete (X)
  - Dark mode and orange accents
- API wiring
  - Frontend calls `/api/*` (proxied to FastAPI)
  - Optimistic updates (UI updates first; reverts on error)
- Data persistence
  - Tasks saved to a JSON file on the server
  - File path can be set with `TASKS_FILE` env var

## Run Locally (Dev)

- Backend
  ```bash
  cd projects/Multicloud-DevOps-Demo/app
  pip install -r ../requirements.txt
  uvicorn main:app --reload --port 8000
  ```

- Frontend
  ```bash
  cd projects/Multicloud-DevOps-Demo/frontend
  npm ci
  npm run dev
  ```

Open: Frontend http://localhost:5173  |  API http://127.0.0.1:8000

## Run with Docker

```bash
cd projects/Multicloud-DevOps-Demo
docker compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000
- Tasks persist in a Docker volume (`/data/tasks.json`)

## Package for AWS Lambda

```bash
cd projects/Multicloud-DevOps-Demo
bash scripts/build_lambda.sh
```

- Upload `lambda.zip` to a Python 3.12 Lambda
- Handler: `app.main.handler`
- For temporary file writes, set env: `TASKS_FILE=/tmp/tasks.json`

## API (FastAPI)

- `GET /health` – health check
- `GET /tasks/` – list tasks
- `POST /tasks/` – create task (expects `{ id, title, completed }`)
- `GET /tasks/{id}` – get one
- `PUT /tasks/{id}` – update task
- `DELETE /tasks/{id}` – remove task

Task model: `id: int`, `title: str`, `completed: bool = False`

## AWS Deployment (Simple)

- Frontend (CloudFront): https://d3lfv4me48i7vz.cloudfront.net
- API (API Gateway): https://xsryp4wqxi.execute-api.us-east-1.amazonaws.com

Deploy updates
- Backend:
  - From repo root: `bash scripts/build_lambda.sh` → upload `lambda.zip` to Lambda (Python 3.12, handler `app.main.handler`).
  - Set env `ALLOW_ORIGINS=https://d3lfv4me48i7vz.cloudfront.net` so CORS allows the site.
- Frontend:
  - In `frontend/.env.production`, set `VITE_API_BASE` to the API URL above.
  - `npm run build` and upload `frontend/dist/` to S3, then invalidate CloudFront.

## AWS Deployment (Simple)

- Frontend (CloudFront): https://d3lfv4me48i7vz.cloudfront.net
- API (API Gateway): https://xsryp4wqxi.execute-api.us-east-1.amazonaws.com

Deploy updates
- Backend:
  - From repo root: `bash scripts/build_lambda.sh` → uploads `lambda.zip` to the Lambda (Python 3.12, handler `app.main.handler`).
  - Set env `ALLOW_ORIGINS=https://d3lfv4me48i7vz.cloudfront.net` so CORS allows the site.
- Frontend:
  - In `frontend/.env.production`, set `VITE_API_BASE` to the API URL above.
  - `npm run build` and upload `frontend/dist/` to your S3 site bucket, then invalidate CloudFront.
