from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import sys
from fastapi_limiter import FastAPILimiter
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, select, delete as sql_delete
from fastapi_limiter.depends import RateLimiter
try:
    from .logging_splunk import log_event  # when executed as app.main
except Exception:
    # Fallback for local runs executed as a script
    from logging_splunk import log_event  # type: ignore

# --- Database (Supabase Postgres) ---
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g., postgresql://... from Supabase
engine = None
SessionLocal = None

if DATABASE_URL:
    # Use async driver
    ASYNC_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(ASYNC_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class TaskORM(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
  start = time.perf_counter()
  response = await call_next(request)
  try:
    if os.getenv("ENABLE_SPLUNK_LOGGING") == "1":
      client_ip = request.headers.get("x-forwarded-for", request.client.host if getattr(request, "client", None) else None)
      log_event("http_request", {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": client_ip,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
      })
  except Exception as e:
    if os.getenv("DEBUG"):
      print(f"Splunk log failed (request): {e}", file=sys.stderr)
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

@app.on_event("startup")
async def _load_on_startup():
    if os.getenv("REDIS_URL"):
        redis = await aioredis.from_url(os.getenv("REDIS_URL"))
        await FastAPILimiter.init(redis)
    # Ensure tables exist (safe for demos)
    if engine is not None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    async with SessionLocal() as session:
        yield session

# Create a task
@app.post("/tasks/", response_model=Task, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_task(task: Task, db: AsyncSession = Depends(get_db)):
    # Ensure unique id if client provides one
    result = await db.execute(select(TaskORM).where(TaskORM.id == task.id))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Task with this ID already exists")
    db_obj = TaskORM(id=task.id, title=task.title, completed=task.completed)
    db.add(db_obj)
    await db.commit()
    try:
        log_event("task_created", {"id": task.id, "title": task.title, "completed": task.completed})
    except Exception as e:
        if os.getenv("DEBUG"):
            print(f"Splunk log failed (create): {e}", file=sys.stderr)
    return task

# Get all tasks
@app.get("/tasks/", response_model=list[Task])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskORM).order_by(TaskORM.id))
    rows = result.scalars().all()
    return [Task(id=r.id, title=r.title, completed=r.completed) for r in rows]

# Get a single task by ID
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task(id=row.id, title=row.title, completed=row.completed)

# Update a task by ID
@app.put("/tasks/{task_id}", response_model=Task, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def update_task(task_id: int, updated_task: Task, db: AsyncSession = Depends(get_db)):
    if updated_task.id != task_id:
        raise HTTPException(status_code=400, detail="Task ID in body must match URL")
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    row.title = updated_task.title
    row.completed = updated_task.completed
    await db.commit()
    try:
        log_event("task_updated", {"id": updated_task.id, "title": updated_task.title, "completed": updated_task.completed})
    except Exception as e:
        if os.getenv("DEBUG"):
            print(f"Splunk log failed (update): {e}", file=sys.stderr)
    return updated_task

# Delete a task by ID
@app.delete("/tasks/{task_id}", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskORM).where(TaskORM.id == task_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.execute(sql_delete(TaskORM).where(TaskORM.id == task_id))
    await db.commit()
    try:
        log_event("task_deleted", {"id": task_id})
    except Exception as e:
        if os.getenv("DEBUG"):
            print(f"Splunk log failed (delete): {e}", file=sys.stderr)
    return {"detail": "Task deleted"}

# Example Splunk Dashboard SPL:
# index="main" sourcetype="http_request"
# | timechart count by status
# | eval latency_bucket=round(latency_ms/100,0)*100
# | timechart avg(latency_ms) by path
