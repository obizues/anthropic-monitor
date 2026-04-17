FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY monitor.config.json .

# Runtime state volumes — mount these externally to persist across container restarts
VOLUME ["/app/state", "/app/queue"]

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
