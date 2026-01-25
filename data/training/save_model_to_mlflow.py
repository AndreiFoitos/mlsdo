import os
import mlflow
import transformers
import torch

MLFLOW_TRACKING_URL = os.getenv('MLFLOW_TRACKING_URL', 'http://localhost:5000')
MLFLOW_MODEL_NAME = os.getenv('MLFLOW_MODEL_NAME', 'add_detection_model')
MODEL_NAME = "distilbert-base-uncased"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URL)

print("Loading trained model from checkpoint...")
checkpoint_path = "./training_logs/checkpoint-2060"

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)
model = transformers.AutoModelForSequenceClassification.from_pretrained(checkpoint_path)

print("Creating MLflow run...")
with mlflow.start_run(run_name=f"model_registration"):
    print("Logging PyTorch model...")
    mlflow.pytorch.log_model(
        model,
        artifact_path='trained-model',
        registered_model_name=MLFLOW_MODEL_NAME
    )

    print("Logging Transformers pipeline...")
    mlflow.transformers.log_model(
        transformers.pipeline('text-classification', model=model, tokenizer=tokenizer),
        artifact_path="pipeline"
    )

print("Model saved successfully!")
