# Knowledge Base API — Google Cloud Run (and local docker build)
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Models download on first request (avoids Cloud Build OOM). Cold start is slower once.

COPY backend ./backend
COPY documents ./documents
COPY scripts ./scripts
COPY indexdir ./indexdir
COPY pytest.ini .

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
