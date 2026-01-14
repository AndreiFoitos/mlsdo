import os
import fastapi
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from celery import Celery
from celery.result import AsyncResult
from prometheus_fastapi_instrumentator import Instrumentator

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class IssueRequest(BaseModel):
    summary: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class PredictionSubmitResponse(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.PENDING

class PredictionStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

app = fastapi.FastAPI(title="ADD Detection API")
Instrumentator().instrument(app).expose(app)

def safe_result(obj: Any) -> Optional[Dict[str, Any]]:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    # fallback: stringify anything else
    return {"value": str(obj)}

@app.post("/predictions", status_code=202, response_model=PredictionSubmitResponse)
async def predict_async(issue: IssueRequest) -> PredictionSubmitResponse:
    task = celery_app.send_task(
        "tasks.classify_issue",
        args=[issue.summary, issue.description]
    )
    return PredictionSubmitResponse(task_id=str(task.id), status=TaskStatus.PENDING)

@app.get("/predictions/{task_id}", response_model=PredictionStatusResponse)
async def get_prediction_status(task_id: str) -> PredictionStatusResponse:
    task_result = AsyncResult(task_id, app=celery_app)
    status = TaskStatus(task_result.status) if task_result.status in TaskStatus.__members__ else TaskStatus.STARTED

    if status in (TaskStatus.PENDING, TaskStatus.STARTED):
        return PredictionStatusResponse(task_id=task_id, status=status)

    if status == TaskStatus.SUCCESS:
        return PredictionStatusResponse(
            task_id=task_id,
            status=status,
            result=safe_result(task_result.result),
            error=None
        )

    # FAILURE: ensure JSON-safe error
    err = str(task_result.result) if task_result.result is not None else "Unknown error"
    return PredictionStatusResponse(task_id=task_id, status=TaskStatus.FAILURE, result=None, error=err)

@app.get("/hello")
async def say_hello():
    return {"message": "hello"}

# trigger build_app
# trigger deploy_api
