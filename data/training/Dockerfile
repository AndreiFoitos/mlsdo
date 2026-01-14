FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    torch==2.0.1 \
    transformers==4.30.0 \
    mlflow==2.9.2 \
    datasets \
    psycopg2-binary \
    scikit-learn \
    torchmetrics \
    numpy \
    accelerate>=0.20.1

COPY ppl-train.py /app/ppl-train.py

CMD ["python", "ppl-train.py"]