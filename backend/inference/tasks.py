import os
import time
from typing import Optional, Tuple

import torch
import mlflow
import mlflow.pytorch
import transformers
import psycopg2
from celery import Celery, Task


REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

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
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

UPSERT_STARTED_SQL = """
INSERT INTO predictions (task_id, summary, description, status)
VALUES (%s, %s, %s, %s)
ON CONFLICT (task_id)
DO UPDATE SET
    summary = EXCLUDED.summary,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;
"""

UPDATE_SUCCESS_SQL = """
UPDATE predictions
SET label = %s,
    probability = %s,
    status = %s,
    error = NULL,
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


def _get_tracking_uri() -> Optional[str]:
    """
    Be compatible with both env var names:
    - MLFLOW_TRACKING_URI (common in MLflow docs)
    - MLFLOW_TRACKING_URL (some projects use this)
    """
    return os.environ.get("MLFLOW_TRACKING_URI") or os.environ.get("MLFLOW_TRACKING_URL")


def _db_connect():
    return psycopg2.connect(POSTGRES_URL)


def _ensure_predictions_table_once():
    """
    Create predictions table once per worker process to avoid repeated DDL.
    """
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


def _mark_success(task_id: str, label: str, probability: float):
    conn = _db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(UPDATE_SUCCESS_SQL, (label, float(probability), "SUCCESS", task_id))
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
        # Init DB table once per worker
        if not self.__class__._db_initialized:
            _ensure_predictions_table_once()
            self.__class__._db_initialized = True

        # Load model/tokenizer once per worker
        if self.__class__._model is None:
            tracking_uri = _get_tracking_uri()
            if not tracking_uri:
                raise RuntimeError("Missing MLflow tracking URI. Set MLFLOW_TRACKING_URI (or MLFLOW_TRACKING_URL).")

            mlflow.set_tracking_uri(tracking_uri)

            model_name = os.environ.get("MLFLOW_MODEL_NAME")
            if not model_name:
                raise RuntimeError("Missing MLFLOW_MODEL_NAME environment variable.")

            model_version = os.environ.get("MLFLOW_MODEL_VERSION", "1")
            model_uri = f"models:/{model_name}/{model_version}"

            # Load PyTorch model from MLflow registry
            self.__class__._model = mlflow.pytorch.load_model(model_uri)

            # Tokenizer (kept as before)
            self.__class__._tokenizer = transformers.AutoTokenizer.from_pretrained("distilbert-base-uncased")

            self.__class__._device = "cuda" if torch.cuda.is_available() else "cpu"
            self.__class__._model.to(self.__class__._device)
            self.__class__._model.eval()

            print(f"[worker] Loaded model {model_uri} on device={self.__class__._device}")

        return self.__class__._model, self.__class__._tokenizer

    @property
    def device(self) -> str:
        # device is set when model is loaded
        return self.__class__._device or "cpu"


@celery_app.task(base=MLModelTask, name="tasks.classify_issue", bind=True)
def classify_issue(self, summary, description):
    """
    Performs DistilBERT inference on the provided issue.
    Persists task metadata + result into Postgres table `predictions`.
    """
    task_id = getattr(self.request, "id", None) or "unknown-task-id"

    # Always write STARTED metadata first (idempotent upsert)
    try:
        _mark_started(task_id, str(summary), str(description))
    except Exception as e:
        # DB write failure shouldn't hide inference entirely, but should be visible in logs
        print(f"[worker] WARNING: failed to write STARTED to DB for task_id={task_id}: {e}")

    start_t = time.time()

    try:
        model, tokenizer = self.model_and_tokenizer

        text = f"{summary}. {description}"
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
            "label": "ADD" if prediction == 1 else "NON-ADD"
        }

        # Persist success
        try:
            _mark_success(task_id, result["label"], result["probability"])
        except Exception as e:
            print(f"[worker] WARNING: failed to write SUCCESS to DB for task_id={task_id}: {e}")

        dur = time.time() - start_t
        print(f"[worker] task_id={task_id} SUCCESS in {dur:.3f}s label={result['label']} prob={result['probability']:.4f}")

        return result

    except Exception as e:
        # Persist failure, then re-raise so Celery marks it as FAILURE
        err_msg = str(e)
        try:
            _mark_failure(task_id, err_msg)
        except Exception as db_e:
            print(f"[worker] WARNING: failed to write FAILURE to DB for task_id={task_id}: {db_e}")

        print(f"[worker] task_id={task_id} FAILURE error={err_msg}")
        raise
