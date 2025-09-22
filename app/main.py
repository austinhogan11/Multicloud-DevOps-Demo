from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Create a FastAPI app instance
app = FastAPI()

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

# Create a task
@app.post("/tasks/", response_model=Task)
def create_task(task: Task):
    if task.id in tasks:
        raise HTTPException(status_code=400, detail="Task with this ID already exists")
    tasks[task.id] = task
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
    return updated_task

# Delete a task by ID
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"detail": "Task deleted"}