FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pandas \
    psycopg2-binary

COPY preprocessing/ppl-load_data.py /app/ppl-load_data.py

RUN mkdir -p /app/data

CMD ["python", "ppl-load_data.py"]