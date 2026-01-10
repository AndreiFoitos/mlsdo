FROM mambaorg/micromamba:debian12-slim

WORKDIR /app

USER root
RUN mkdir -p /app && chown -R 1000:1000 /app

COPY environment.yml .

RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

USER 1000

COPY --chown=1000:1000 ./backend/inference/tasks.py .

ENV PATH="/opt/conda/bin:$PATH"

CMD ["micromamba", "run", "-n", "base", "celery", "-A", "backend.inference.tasks", "worker", "--loglevel=info"]
