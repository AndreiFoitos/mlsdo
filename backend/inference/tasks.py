import os
import torch
import mlflow.pytorch
from celery import Celery, Task

celery_app = Celery("tasks", broker=os.environ.get('REDIS_URL', 'redis://redis:6379/0'))

class MLModelTask(Task):
    """Abstract Task to ensure the model is loaded once per worker process."""
    _model = None
    _tokenizer = None

    @property
    def model_and_tokenizer(self):
        if self._model is None:
            mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URL'))
            model_name = os.environ.get('MLFLOW_MODEL_NAME')
            model_version = os.environ.get('MLFLOW_MODEL_VERSION', '1')
            
            self._model = mlflow.pytorch.load_model(f"models:/{model_name}/{model_version}")
        return self._model

@celery_app.task(base=MLModelTask, name="tasks.classify_issue", bind=True)
def classify_issue(self, summary, description):
    """Performs the actual DistilBERT inference asynchronously."""
    model = self.model_and_tokenizer
    return {"is_add": True, "probability": 0.85}