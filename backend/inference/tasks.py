import os
import torch
import mlflow.pytorch
import transformers
from celery import Celery, Task


REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)
class MLModelTask(Task):
    """Abstract Task to ensure the model and tokenizer are loaded once per worker."""
    _model = None
    _tokenizer = None

    @property
    def model_and_tokenizer(self):
        if self._model is None:
            mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URL'))
            model_name = os.environ.get('MLFLOW_MODEL_NAME')
            model_version = os.environ.get('MLFLOW_MODEL_VERSION', '1')
            
            model_uri = f"models:/{model_name}/{model_version}"
            self._model = mlflow.pytorch.load_model(model_uri)
            
            self._tokenizer = transformers.AutoTokenizer.from_pretrained("distilbert-base-uncased")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self.device)
            self._model.eval()
            
        return self._model, self._tokenizer

@celery_app.task(base=MLModelTask, name="tasks.classify_issue", bind=True)
def classify_issue(self, summary, description):
    """Performs DistilBERT inference on the provided issue[cite: 137]."""
    model, tokenizer = self.model_and_tokenizer
    
    text = f"{summary}. {description}"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding="max_length")
    inputs = {k: v.to(self.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=-1)
        prediction = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][prediction].item()

    return {
        "is_add": bool(prediction == 1), 
        "probability": float(confidence),
        "label": "ADD" if prediction == 1 else "NON-ADD"
    }
# trigger build_train_image
