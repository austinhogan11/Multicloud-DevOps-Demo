# Multicloud DevOps Demo

Simple Todo app to show a full stack:

- Backend: FastAPI Tasks API
- Frontend: React + Vite + Tailwind
- Persistence: JSON file (survives restarts)
- Docker: Frontend (Nginx) + Backend (Uvicorn) with Compose

## Preview

<img src="docs/todo-app.png" alt="Todo App UI" />

## Live URLs

- Frontend (CloudFront): https://d340jwtq80qp5u.cloudfront.net/
- API (API Gateway): https://m49frfvff3.execute-api.us-east-1.amazonaws.com

## Architecture

The app is a small full‑stack deployed to AWS with Terraform and GitHub Actions.

```mermaid
flowchart LR

  %% CI/CD orchestrator
  GH[GitHub Actions] --> TF

  %% Left-to-right: Frontend | API | Backend
  subgraph FE[Frontend]
    R[React.js] --> UI[Todo UI]
    V[Vite] --> UI
    T[TailwindCSS] --> UI
  end

  subgraph API[API]
    Task[Task API]
  end

  subgraph BE[Backend]
    Py[Python] --> FAPI[FastAPI]
  end

  %% Bidirectional wiring
  UI <--> Task
  FAPI <--> Task

  %% Terraform beneath the three sections
  subgraph TF[Terraform]
  end

  FE --> TF
  API --> TF
  BE --> TF

  %% Provision into AWS
  TF --> AWS

  subgraph AWS[AWS]
    direction TB
    %% Frontend in AWS
    subgraph AWS_FE[Frontend]
      direction TB
      CF[CloudFront] --> S3[S3]
      CF --> CFURL[Frontend URL: d340jwtq80qp5u.cloudfront.net]
    end

    %% API in AWS
    subgraph AWS_API[API]
      direction TB
      APIGW[API Gateway] --> APIURL[API URL: m49frfvff3.execute-api.us-east-1.amazonaws.com]
    end

    %% Backend in AWS
    subgraph AWS_BE[Backend]
      direction TB
      LMB[Lambda] --> CW[CloudWatch]
    end

    %% Terraform backend (part of AWS)
    TFS3[S3 TF State]
    TFDDB[DynamoDB Lock]
  end
```

## Delivery Timeline (Sprints)

- Sprint 1: Backend + API
  - FastAPI Tasks API with health and CRUD endpoints
  - JSON persistence (local file) and Mangum handler for Lambda
- Sprint 2: Frontend
  - React + Vite + Tailwind SPA (dark theme, optimistic UI updates)
  - Clean components and minimal state, API client stub
- Sprint 3: Wire API between front and back
  - VITE_API_BASE and dev proxy; error handling and retries
  - CORS configured in FastAPI; validated with browser and curl
- Sprint 4: Infrastructure as Code (Terraform on AWS)
  - S3 (static site), CloudFront (OAC), API Gateway (HTTP API), Lambda, IAM
  - Remote state (S3) + optional DynamoDB lock; outputs for API/CDN/ bucket
- Sprint 5: CI/CD (GitHub Actions)
  - OIDC AssumeRole; build lambda.zip via SAM image; terraform init/apply
  - Build frontend with VITE_API_BASE from TF output; S3 sync; CF invalidate
  - Sanity steps: backend resources, API health probe, bundle URL check, CORS preflight
- Sprint 6: Analytics
  - Plausible integration pattern documented; ready to plug in custom domains
- Sprint 7: Monitoring
  - CloudWatch logs; hook points for Splunk/third‑party ingestion

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

## Deployments

We use GitHub Actions + Terraform to deploy infra and app end‑to‑end.

- Workflow: `.github/workflows/deploy-stack.yml`
  - Builds `build/lambda.zip` in a Linux (x86_64) container for Lambda
  - Terraform init/apply with S3 state and optional DynamoDB lock
  - Reads TF outputs and sets `VITE_API_BASE` for the frontend build
  - Syncs frontend to S3 and invalidates CloudFront
  - Verifies CORS and API health in CI logs

- Secrets/variables needed
  - Secret `AWS_ROLE_ARN`: OIDC‑assumable role ARN
  - Vars `TF_STATE_BUCKET`, `TF_STATE_KEY`, optional `TF_LOCK_TABLE`
  - Optional fallbacks: `LAMBDA_FUNCTION`, `S3_BUCKET`, `CF_DISTRIBUTION_ID` (used if TF is skipped)

- CORS and config
  - Lambda env `ALLOW_ORIGINS` is auto‑set by Terraform to the CloudFront domain
  - `frontend` build sets `VITE_API_BASE` from TF output (API Gateway invoke URL)

Note: Terraform ignores Lambda `filename`/`source_code_hash` so CI can update code without perpetual diffs.

## Delivery Timeline (Sprints)

- Sprint 1: Backend + API
  - FastAPI “Tasks” service with health, CRUD, JSON persistence
  - Packaged for AWS Lambda using Mangum handler
- Sprint 2: Frontend
  - React + Vite + Tailwind SPA with dark theme and optimistic UI
- Sprint 3: Wire API between front and back
  - API client, error handling, env‑driven API base
- Sprint 4: Infrastructure as Code (Terraform)
  - S3 (static site), CloudFront (OAC), API Gateway (HTTP API), Lambda, IAM
  - Remote state backend: S3 + optional DynamoDB lock
- Sprint 5: CI/CD (GitHub Actions)
  - OIDC AssumeRole; build lambda.zip; Terraform apply; build frontend; S3 sync; CF invalidate
  - Sanity checks and verification steps (API health, CORS, bundle URL check)
- Sprint 6: Analytics
  - Plausible analytics wired (example integration pattern)
- Sprint 7: Monitoring
  - Placeholder for Splunk (ship logs/metrics from Lambda, infra states)
