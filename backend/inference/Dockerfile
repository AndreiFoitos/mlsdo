FROM mambaorg/micromamba:debian12-slim

WORKDIR /app

USER root
RUN mkdir -p /app && chown -R 1000:1000 /app

COPY environment.yml .

RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

USER 1000

COPY ./backend/inference ./backend/inference
COPY ./data/training ./data/training

ENV PATH="/opt/conda/bin:$PATH"
ENV POSTGRES_URL=postgresql://postgres:pw1@postgres-ml:5432/reviews_db
ENV MLFLOW_TRACKING_URL=http://mlflow:5000
ENV MLFLOW_MODEL_NAME=add_detection_model

CMD ["micromamba", "run", "-n", "base", "celery", "-A", "backend.inference.tasks", "worker", "--loglevel=info"]
