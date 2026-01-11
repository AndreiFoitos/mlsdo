FROM mambaorg/micromamba:debian12-slim

WORKDIR /app

USER root
RUN mkdir -p /app && chown -R 1000:1000 /app

COPY ../environment.yml .
RUN micromamba install -y -n base -f environment.yml && micromamba clean --all --yes

USER 1000
COPY --chown=1000:1000 ./backend/api/app.py .

ENV REDIS_URL=redis://redis:6379/0
EXPOSE 8080

CMD ["micromamba", "run", "-n", "base", "python", "-m", "fastapi", "run", "app.py", "--host", "0.0.0.0", "--port", "8080", "--app", "app"]