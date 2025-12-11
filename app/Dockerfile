FROM mambaorg/micromamba:debian12-slim

WORKDIR /app

USER root
RUN mkdir -p /app && chmod -R 777 /app

COPY environment.yml .

RUN micromamba install -y -n base -f environment.yml && micromamba clean --all --yes

COPY app.py .
COPY ppl-train.py .
COPY ppl-load_data.py .

# Environment variables for loading data (TODO Set ENVs from ARG's)
# Must mount a volume at "/data" with access to the dataset
ENV DATASET_FILEPATH=/data/book_reviews-10k.jsonl
ENV DB_NAME=reviews_db
ENV DB_USER=postgres
ENV DB_PASSWORD=pw1
ENV DB_HOST=postgres-ml
ENV DB_PORT=5432

# Environment variables for training and api  (TODO Set ENVs from ARG's)
ENV POSTGRES_URL="postgresql://postgres:pw1@postgres-ml:5432/reviews_db"
ENV MLFLOW_MODEL_NAME=review-prediction-model
ENV MLFLOW_TRACKING_URL=http://mlflow:5000

# Ideally you want to automate loading the latest production model
ENV MLFLOW_MODEL_VERSION=1

EXPOSE 8080

## To run the load_data pipeline
# docker run -d --network mlsdo-lab5_lab5 -v /home/daniel/app/data:/data <image-name> python ppl-load_data.py

## To run the training pipeline
# docker run -d --network mlsdo-lab5_lab5 <image-name> python ppl-train.py

## To run the fastapi app
# docker run -d --network mlsdo-lab5_lab5 -p 8080:8080 <image-name> python -m fastapi run app.py --host 0.0.0.0 --port 8080 --app app
