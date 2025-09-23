# Multicloud DevOps Demo

Simple Todo app to show a full stack:

- Backend: FastAPI Tasks API
- Frontend: React + Vite + Tailwind
- Persistence: JSON file (survives restarts)
- Docker: Frontend (Nginx) + Backend (Uvicorn) with Compose

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

## API (FastAPI)

- `GET /health` – health check
- `GET /tasks/` – list tasks
- `POST /tasks/` – create task (expects `{ id, title, completed }`)
- `GET /tasks/{id}` – get one
- `PUT /tasks/{id}` – update task
- `DELETE /tasks/{id}` – remove task

Task model: `id: int`, `title: str`, `completed: bool = False`

