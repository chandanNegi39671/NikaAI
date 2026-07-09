# ==============================================================================
# NikaAI Backend Dockerfile
# Multi-stage build for FastAPI + YOLO + Celery
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1 - Build Dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .

RUN echo "========== REQUIREMENTS ==========" && cat requirements.txt

RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2 - Runtime Image
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Runtime libraries required by OpenCV / YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Create application user
RUN groupadd --system nikaai && \
    useradd --system --gid nikaai --create-home nikaai

# Copy project
COPY --chown=nikaai:nikaai . .

# Create required folders
RUN mkdir -p \
    static/uploads \
    logs \
    app/models && \
    chown -R nikaai:nikaai /app

USER nikaai

# Expose API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start FastAPI via Gunicorn + UvicornWorker
# Using Gunicorn as process manager so worker processes are forked BEFORE
# PyTorch / YOLO is imported. This avoids CUDA context corruption and thread
# lock deadlocks that occur when forking after torch initialisation.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--log-level", "info"]