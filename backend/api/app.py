import os
import fastapi
from pydantic import BaseModel
from celery import Celery
from celery.result import AsyncResult
from prometheus_fastapi_instrumentator import Instrumentator

REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

class IssueRequest(BaseModel):
    summary: str
    description: str

class PredictionResponse(BaseModel):
    task_id: str
    status: str

app = fastapi.FastAPI(title="ADD Detection API")

Instrumentator().instrument(app).expose(app)

@app.post('/predictions', status_code=202)
async def predict_async(issue: IssueRequest) -> PredictionResponse:
    """
    Submits a prediction task to the Celery worker.
    Returns 202 Accepted immediately to ensure responsiveness.
    """
    task = celery_app.send_task(
        "tasks.classify_issue", 
        args=[issue.summary, issue.description]
    )
    return PredictionResponse(task_id=str(task.id), status="PENDING")

@app.get('/predictions/{task_id}')
async def get_prediction_status(task_id: str):
    """
    Check the status or retrieve the result of an asynchronous task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }

@app.get('/hello')
async def say_hello():
    return {'message': 'hello'}# test deploy
# trigger build_app
# trigger deploy_api
# trigger build_app
# trigger deploy_api
