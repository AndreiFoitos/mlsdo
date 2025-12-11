import contextlib
import os

import fastapi
import mlflow
import pandas as pd
import psycopg2
import pydantic
import torch
import transformers

MODEL_NAME = "google/bert_uncased_L-2_H-128_A-2"
db_connection = None
model = None
tokenizer = None
device = None


class Review(pydantic.BaseModel):
    title: str
    text: str


class PredictionResponse(pydantic.BaseModel):
    sentiment: bool
    probability: float


@contextlib.asynccontextmanager
async def lifespan(app):
    global db_connection, model, tokenizer, device
    
    # Database connection
    db_url = os.environ.get('POSTGRES_URL', None)
    if db_url is None:
        raise ValueError('POSTGRES_URL environment variable not set')
    db_connection = psycopg2.connect(db_url)

    # Create ml_ratings table if it doesn't exist
    with db_connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_ratings (
            title TEXT, 
            text TEXT, 
            sentiment BOOLEAN
        )""")

    # Tokenizer and device
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)
    device = torch.device("cpu") # force CPU (in case GPU is default)

    # MLflow model
    mlflow_tracking_url = os.environ.get('MLFLOW_TRACKING_URL', None)
    if mlflow_tracking_url is None:
        raise ValueError('MLFLOW_TRACKING_URL environment variable not set')
    mlflow.set_tracking_uri(mlflow_tracking_url)

    model_name = os.environ.get('MLFLOW_MODEL_NAME')
    model_version = os.environ.get('MLFLOW_MODEL_VERSION')
    model = mlflow.pytorch.load_model(f"models:/{model_name}/{model_version}")

    try:
        yield
    finally:
        db_connection.close()


app = fastapi.FastAPI(lifespan=lifespan)


@app.get('/hello')
async def say_hello():
    return {'message': 'hello'}


@app.post('/predict')
def predict_and_store(review: Review) -> PredictionResponse:
    global model, db_connection, tokenizer, device
    if model is None:
        raise ValueError("Model is not loaded")

    # Tokenize the input text
    tokenized = tokenizer(
        f"{review.title}. {review.text}",
        padding="max_length",
        max_length=512,
        truncation=True,
        add_special_tokens=True,
        return_tensors="pt"  # Return PyTorch tensors
    )
    
    model = model.to(device)
    tokenized = {key: value.to(device) for key, value in tokenized.items()}
    model.eval()  # Ensure the model is in evaluation mode
    with torch.no_grad():
        out = model(**tokenized)
        probabilities = torch.nn.functional.sigmoid(out.logits)
        probability = probabilities.squeeze().item()
        prediction = probabilities.round().squeeze().item()

    sentiment = bool(prediction)

    # Store prediction in the database
    with db_connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO ml_ratings (title, text, sentiment) '
            'VALUES (%s, %s, %s)',
            (review.title, review.text, sentiment)
        )
    return PredictionResponse(sentiment=sentiment, probability=probability)
