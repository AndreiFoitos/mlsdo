FROM mambaorg/micromamba:debian12-slim

WORKDIR /app

USER root
RUN mkdir -p /app && chown -R 1000:1000 /app

COPY environment.yml .
RUN micromamba install -y -n base -f environment.yml && micromamba clean --all --yes

USER 1000

COPY ./backend/api ./backend/api

ENV REDIS_URL=redis://redis:6379/0
ENV PATH="/opt/conda/bin:$PATH"
EXPOSE 8080

CMD ["micromamba", "run", "-n", "base", "python", "-m", "uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
