from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pathlib import Path
import os
import json
import threading

# Create a FastAPI app instance
app = FastAPI()

# Allow the Vite dev server to call this API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a root endpoint that returns a welcome message
@app.get("/")
def read_root():
    return {"message": "Hello from Multicloud DevOps Demo!"}

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
    return updated_task

# Delete a task by ID
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    save_tasks()
    return {"detail": "Task deleted"}
