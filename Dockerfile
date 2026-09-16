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

# Healthcheck (respects dynamic PORT)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; p = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health')" || exit 1

CMD ["sh", "-c", "gunicorn backend.app:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]
