from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pathlib import Path
import os
import json
import threading
from typing import Any, Dict, Optional
try:
    from .logging_splunk import log_event  # when executed as app.main
except Exception:
    # Fallback for local runs executed as a script
    from logging_splunk import log_event  # type: ignore

# Create a FastAPI app instance
app = FastAPI()

# Allow the frontend to call this API (CORS)
# In production, set ALLOW_ORIGINS to a comma-separated list (e.g.,
# "https://dxxxx.cloudfront.net,https://mydomain.com").
_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_allow_env = os.getenv("ALLOW_ORIGINS", "")
if _allow_env:
    _origins += [o.strip() for o in _allow_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logger(request, call_next):
  response = await call_next(request)
  try:
    log_event("http_request", {
      "method": request.method,
      "path": request.url.path,
      "status": response.status_code,
      "user_agent": request.headers.get("user-agent"),
    })
  except Exception:
    pass
  return response

# Optional AWS Lambda handler (active in Lambda or when ENABLE_MANGUM=1)
try:
    from mangum import Mangum  # type: ignore
    _has_mangum = True
except Exception:
    _has_mangum = False

if _has_mangum and (os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("ENABLE_MANGUM") == "1"):
    # Expose `handler` for AWS Lambda runtime
    handler = Mangum(app)


# Define a health check endpoint that returns service status
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Define a Task model using Pydantic BaseModel
class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

# In-memory storage for tasks
tasks = {}

# Simple local persistence to a JSON file
# By default, write next to this module. Can be overridden via env var.
TASKS_FILE = Path(os.getenv("TASKS_FILE", str(Path(__file__).with_name("tasks.json"))))
_lock = threading.Lock()

def save_tasks() -> None:
    data = jsonable_encoder(list(tasks.values()))
    tmp = TASKS_FILE.with_suffix(".tmp")
    with _lock:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(TASKS_FILE)

def load_tasks() -> None:
    if not TASKS_FILE.exists():
        return
    try:
        raw = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        tasks.clear()
        for item in raw:
            t = Task(**item)
            tasks[t.id] = t
    except Exception:
        tasks.clear()

@app.on_event("startup")
def _load_on_startup():
    load_tasks()

# Create a task
@app.post("/tasks/", response_model=Task)
def create_task(task: Task):
    if task.id in tasks:
        raise HTTPException(status_code=400, detail="Task with this ID already exists")
    tasks[task.id] = task
    save_tasks()
    try:
        log_event("task_created", {"id": task.id, "title": task.title, "completed": task.completed})
    except Exception:
        pass
    return task

# Get all tasks
@app.get("/tasks/", response_model=list[Task])
def get_tasks():
    return list(tasks.values())

# Get a single task by ID
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

# Update a task by ID
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, updated_task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    if updated_task.id != task_id:
        raise HTTPException(status_code=400, detail="Task ID in body must match URL")
    tasks[task_id] = updated_task
    save_tasks()
    try:
        log_event("task_updated", {"id": updated_task.id, "title": updated_task.title, "completed": updated_task.completed})
    except Exception:
        pass
    return updated_task

# Delete a task by ID
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    save_tasks()
    try:
        log_event("task_deleted", {"id": task_id})
    except Exception:
        pass
    return {"detail": "Task deleted"}
