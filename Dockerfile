# ==============================================================================
# PeerSpace Production Dockerfile
# Multi-stage lightweight Python container
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root unprivileged user for security
RUN useradd -m -u 1001 peerspace && \
    chown -R peerspace:peerspace /app

# Copy installed wheels from builder
COPY --from=builder /root/.local /home/peerspace/.local
ENV PATH=/home/peerspace/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Copy application source code
COPY --chown=peerspace:peerspace . /app

USER peerspace

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["gunicorn", "backend.app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
