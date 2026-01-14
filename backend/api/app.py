import os
import fastapi
<<<<<<< HEAD
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
=======
from pydantic import BaseModel
from typing import List, Optional
>>>>>>> 4af5320724464626e5a21b80e6db52fb42992732
from celery import Celery
from celery.result import AsyncResult
from prometheus_fastapi_instrumentator import Instrumentator
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

<<<<<<< HEAD
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
=======
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql://postgres:pw1@postgres-ml:5432/reviews_db')
>>>>>>> 4af5320724464626e5a21b80e6db52fb42992732

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

<<<<<<< HEAD
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class IssueRequest(BaseModel):
    summary: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class PredictionSubmitResponse(BaseModel):
=======
# Request/Response Models
class IssueRequest(BaseModel):
    summary: str
    description: str

class BatchIssueRequest(BaseModel):
    issues: List[IssueRequest]

class PredictionResponse(BaseModel):
>>>>>>> 4af5320724464626e5a21b80e6db52fb42992732
    task_id: str
    status: TaskStatus = TaskStatus.PENDING

class PredictionStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

<<<<<<< HEAD
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
=======
class BatchPredictionResponse(BaseModel):
    task_ids: List[str]
    status: str

class LabeledIssueRequest(BaseModel):
    summary: str
    description: str
    label: str  # 'ADD' or 'non-ADD'

app = fastapi.FastAPI(
    title="ADD Detection API",
    description="API for Architectural Design Decision Detection in Jira issues",
    version="1.0.0"
)

# Enable Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Database helper
def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        return psycopg2.connect(POSTGRES_URL)
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500, 
            detail=f"Database connection failed: {str(e)}"
        )

# Health check endpoint
@app.get('/', tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        'status': 'healthy',
        'message': 'ADD Detection API is running',
        'version': '1.0.0'
    }

@app.get('/hello', tags=["Health"])
async def say_hello():
    """Simple hello endpoint for testing"""
    return {'message': 'hello'}
>>>>>>> 4af5320724464626e5a21b80e6db52fb42992732

# ===== PREDICTION ENDPOINTS =====

@app.post('/predictions', status_code=202, tags=["Predictions"])
async def predict_async(issue: IssueRequest) -> PredictionResponse:
    """
    Submit a single prediction task to the Celery worker.
    
    Returns 202 Accepted immediately to ensure responsiveness.
    Client should poll /predictions/{task_id} for results.
    
    - **summary**: Issue summary text
    - **description**: Detailed issue description
    """
    try:
        task = celery_app.send_task(
            "tasks.classify_issue", 
            args=[issue.summary, issue.description]
        )
        return PredictionResponse(task_id=str(task.id), status="PENDING")
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to submit prediction: {str(e)}"
        )

@app.post('/predictions/batch', status_code=202, tags=["Predictions"])
async def predict_batch_async(batch: BatchIssueRequest) -> BatchPredictionResponse:
    """
    Submit multiple prediction tasks to the Celery worker.
    
    Returns 202 Accepted immediately with all task IDs.
    Client should poll /predictions/{task_id} for each task's result.
    
    - **issues**: List of issues to classify
    """
    try:
        task_ids = []
        for issue in batch.issues:
            task = celery_app.send_task(
                "tasks.classify_issue",
                args=[issue.summary, issue.description]
            )
            task_ids.append(str(task.id))
        
        return BatchPredictionResponse(task_ids=task_ids, status="PENDING")
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to submit batch prediction: {str(e)}"
        )

@app.get('/predictions/{task_id}', tags=["Predictions"])
async def get_prediction_status(task_id: str):
    """
    Check the status or retrieve the result of an asynchronous prediction task.
    
    Possible statuses:
    - **PENDING**: Task is waiting to be processed
    - **STARTED**: Task is currently being processed
    - **SUCCESS**: Task completed successfully (result available)
    - **FAILURE**: Task failed (error details in result)
    - **RETRY**: Task is being retried
    
    - **task_id**: The task ID returned from prediction submission
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
        }
        
        # Include result if task is complete
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.result)
        
        return response
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to fetch task status: {str(e)}"
        )

# ===== ISSUE SEARCH ENDPOINTS =====

@app.get('/issues/search', tags=["Issues"])
async def search_issues(
    keyword: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """
    Search for issues in the database using keywords.
    
    Searches in both summary and description fields (case-insensitive).
    
    - **keyword**: Search term to find in issues
    - **limit**: Maximum number of results to return (default: 50)
    - **offset**: Number of results to skip for pagination (default: 0)
    """
    if not keyword or not keyword.strip():
        raise fastapi.HTTPException(
            status_code=400,
            detail="Keyword parameter is required and cannot be empty"
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Search in both summary and description using ILIKE for case-insensitive search
        query = """
            SELECT id, summary, description, label, created_at
            FROM issues
            WHERE summary ILIKE %s OR description ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        search_pattern = f"%{keyword}%"
        cursor.execute(query, (search_pattern, search_pattern, limit, offset))
        
        results = cursor.fetchall()
        
        # Get total count for pagination info
        count_query = """
            SELECT COUNT(*) as total
            FROM issues
            WHERE summary ILIKE %s OR description ILIKE %s
        """
        cursor.execute(count_query, (search_pattern, search_pattern))
        total = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "keyword": keyword
        }
    except psycopg2.Error as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

# ===== LABELED DATA COLLECTION (BONUS) =====

@app.post('/issues/labeled', status_code=201, tags=["Issues"])
async def submit_labeled_issue(issue: LabeledIssueRequest):
    """
    BONUS FEATURE: Collect new labeled data from users.
    
    Stores user-provided labels for model improvement and future retraining.
    This helps create a human-in-the-loop system for continuous learning.
    
    - **summary**: Issue summary text
    - **description**: Detailed issue description  
    - **label**: Ground truth label ('ADD' or 'non-ADD')
    """
    # Validate label
    valid_labels = ['ADD', 'non-ADD']
    if issue.label not in valid_labels:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Invalid label. Must be one of: {valid_labels}"
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the labeled issue into a separate table for retraining
        insert_query = """
            INSERT INTO labeled_issues (summary, description, label, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(
            insert_query, 
            (issue.summary, issue.description, issue.label, datetime.now())
        )
        issue_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "id": issue_id,
            "message": "Labeled issue submitted successfully",
            "summary": issue.summary,
            "label": issue.label,
            "created_at": datetime.now().isoformat()
        }
    except psycopg2.Error as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Database insert failed: {str(e)}"
        )
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to submit labeled issue: {str(e)}"
        )

@app.get('/issues/labeled/count', tags=["Issues"])
async def get_labeled_count():
    """
    Get count of labeled issues collected for model improvement.
    
    Returns total count and breakdown by label type.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total count and breakdown
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN label = 'ADD' THEN 1 ELSE 0 END) as add_count,
                SUM(CASE WHEN label = 'non-ADD' THEN 1 ELSE 0 END) as non_add_count
            FROM labeled_issues
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total": result['total'] or 0,
            "add_count": result['add_count'] or 0,
            "non_add_count": result['non_add_count'] or 0
        }
    except psycopg2.Error as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to get labeled count: {str(e)}"
        )

# ===== STATISTICS ENDPOINTS =====

@app.get('/stats', tags=["Statistics"])
async def get_statistics():
    """
    Get system statistics including total issues and predictions made.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get issue count
        cursor.execute("SELECT COUNT(*) as total FROM issues")
        issues_result = cursor.fetchone()
        
        # Get labeled issues count
        cursor.execute("SELECT COUNT(*) as total FROM labeled_issues")
        labeled_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_issues": issues_result['total'] if issues_result else 0,
            "total_labeled": labeled_result['total'] if labeled_result else 0,
            "api_version": "1.0.0"
        }
    except Exception as e:
        # If tables don't exist yet, return zeros
        return {
            "total_issues": 0,
            "total_labeled": 0,
            "api_version": "1.0.0",
            "note": "Database tables may not be initialized yet"
        }

# trigger build_app
# trigger deploy_api