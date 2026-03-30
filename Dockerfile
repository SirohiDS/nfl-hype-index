FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# Single worker to keep in-memory refresh tick state consistent
# $PORT is set by Render (and other platforms); falls back to 8050 locally
CMD gunicorn app.app:server --bind 0.0.0.0:${PORT:-8050} --workers 1 --timeout 120
