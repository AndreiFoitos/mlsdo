FROM python:3.9-slim

RUN pip install mlflow psycopg2-binary boto3

CMD mlflow server \
    --backend-store-uri $POSTGRES_URL \
    --default-artifact-root s3://$BUCKET \
    --host 0.0.0.0 \
    --port 5000 \
    --serve-artifacts