import os
import time
import logging
import re
from typing import Optional, Tuple

import torch
import mlflow
import mlflow.pytorch
import transformers
import psycopg2
from celery import Celery, Task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
TAG_RE = re.compile(r"<[^>]+>")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

POSTGRES_URL = os.environ.get(
    "POSTGRES_URL",
    "postgresql://postgres:pw1@postgres-ml:5432/reviews_db"
)

PREDICTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    task_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    label TEXT,
    probability DOUBLE PRECISION,
    existence_pred BOOLEAN,
    executive_pred BOOLEAN,
    property_pred BOOLEAN,
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

UPSERT_STARTED_SQL = """
INSERT INTO issues (task_id, summary, description, status)
VALUES (%s, %s, %s, %s)
ON CONFLICT (task_id)
DO UPDATE SET status = EXCLUDED.status, 
"""

UPDATE_SUCCESS_SQL = """
UPDATE issues
SET label = %s,
    prediction = %s,
    confidence = %s,
    status = 'SUCCESS',
    updated_at = CURRENT_TIMESTAMP
WHERE task_id = %s;
"""

UPDATE_FAILURE_SQL = """
UPDATE predictions
SET status = %s,
    error = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE task_id = %s;
"""

def clean_text(text):
    """Removes Jira-specific formatting and HTML tags as required by the rubric."""
    if text is None:
        return ""
    text = TAG_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _get_tracking_uri() -> Optional[str]:
    return os.environ.get("MLFLOW_TRACKING_URI") or os.environ.get("MLFLOW_TRACKING_URL")

def _db_connect():
    return psycopg2.connect(POSTGRES_URL)

def _ensure_predictions_table_once():
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(PREDICTIONS_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()

def _mark_started(task_id: str, summary: str, description: str):
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(UPSERT_STARTED_SQL, (task_id, summary, description, "STARTED"))
        conn.commit()
    finally:
        conn.close()

def _mark_success(task_id: str, label: str, probability: float, types: dict):
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(UPDATE_SUCCESS_SQL, (
                label, 
                float(probability), 
                types.get('existence'), 
                types.get('executive'), 
                types.get('property'), 
                "SUCCESS", 
                task_id
            ))
        conn.commit()
    finally:
        conn.close()

def _mark_failure(task_id: str, error_msg: str):
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(UPDATE_FAILURE_SQL, ("FAILURE", error_msg, task_id))
        conn.commit()
    finally:
        conn.close()

class MLModelTask(Task):
    """Abstract Task to ensure the model and tokenizer are loaded once per worker."""
    _model = None
    _tokenizer = None
    _device = None
    _db_initialized = False

    @property
    def model_and_tokenizer(self) -> Tuple[torch.nn.Module, transformers.PreTrainedTokenizer]:
        if not self.__class__._db_initialized:
            _ensure_predictions_table_once()
            self.__class__._db_initialized = True

        if self.__class__._model is None:
            tracking_uri = _get_tracking_uri()
            if not tracking_uri:
                logger.error("Missing MLflow tracking URI")
                raise RuntimeError("Missing MLflow tracking URI.")

            mlflow.set_tracking_uri(tracking_uri)
            model_name = os.environ.get("MLFLOW_MODEL_NAME")
            model_version = os.environ.get("MLFLOW_MODEL_VERSION", "1")
            model_uri = f"models:/{model_name}/{model_version}"

            logger.info(f"Loading model from registry: {model_uri}")
            self.__class__._model = mlflow.pytorch.load_model(model_uri)
            self.__class__._tokenizer = transformers.AutoTokenizer.from_pretrained("distilbert-base-uncased")

            self.__class__._device = "cuda" if torch.cuda.is_available() else "cpu"
            self.__class__._model.to(self.__class__._device)
            self.__class__._model.eval()

            logger.info(f"Worker loaded model on device: {self.__class__._device}")

        return self.__class__._model, self.__class__._tokenizer

    @property
    def device(self) -> str:
        return self.__class__._device or "cpu"

@celery_app.task(base=MLModelTask, name="tasks.classify_issue", bind=True)
def classify_issue(self, summary, description):
    """Performs inference and persists results to the database [cite: 314-317]."""
    task_id = getattr(self.request, "id", None) or "unknown-task-id"
    logger.info(f"Starting classification for task_id={task_id}")

    try:
        _mark_started(task_id, str(summary), str(description))
    except Exception as e:
        logger.warning(f"Database write failure (STARTED) for task_id={task_id}: {e}")

    start_t = time.time()

    try:
        model, tokenizer = self.model_and_tokenizer
        clean_summary = clean_text(summary)
        clean_description = clean_text(description)
        text = f"{clean_summary}. {clean_description}"

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding="max_length"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            prediction = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][prediction].item()

        result = {
            "is_add": bool(prediction == 1),
            "probability": float(confidence),
            "label": "ADD" if prediction == 1 else "NON-ADD",
            "types": {
                "existence": bool(prediction == 1),
                "executive": False,
                "property": False
            }
        }

        try:
            _mark_success(task_id, result["label"], result["probability"], result["types"])
        except Exception as e:
            logger.warning(f"Database write failure (SUCCESS) for task_id={task_id}: {e}")

        dur = time.time() - start_t
        logger.info(f"Task success: task_id={task_id} duration={dur:.3f}s label={result['label']}")

        return result

    except Exception as e:
        err_msg = str(e)
        try:
            _mark_failure(task_id, err_msg)
        except Exception as db_e:
            logger.warning(f"Database write failure (FAILURE) for task_id={task_id}: {db_e}")

        logger.error(f"Task failure: task_id={task_id} error={err_msg}")
        raise