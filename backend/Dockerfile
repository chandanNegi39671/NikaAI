# ==============================================================================
# NikaAI Backend Dockerfile
# Multi-stage build: builder (compile deps) → runtime (lean image)
#
# Bug fixes in this revision
# ──────────────────────────
# 1. PyTorch CPU wheels require --extra-index-url passed explicitly to pip at
#    install time because Docker BuildKit sometimes reads --extra-index-url
#    lines in requirements.txt in a different order than pip CLI does.
#    Passing the flag explicitly on the CLI guarantees the pytorch wheel index
#    is available when resolving torch==X.Y.Z+cpu version specifiers.
# 2. requirements.txt is copied in its own layer (before source code) so that
#    pip install only re-runs when dependencies actually change.
# 3. start_period raised to 60 s to allow YOLO model load + warmup.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1 — Builder: install Python packages
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build tools needed to compile psycopg2 and some other C-extension packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

# ── Dependency layer (cached unless requirements.txt changes) ─────────────────
COPY requirements.txt .

# Pass --extra-index-url explicitly on the CLI so pip always resolves
# torch==*+cpu version specifiers against the PyTorch CPU wheel index,
# regardless of the order pip reads option lines in requirements.txt.
RUN pip install \
    --no-cache-dir \
    --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2 — Runtime: lean production image
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:$PATH"

# Runtime libraries required by OpenCV / YOLO inference
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create a non-root application user
RUN groupadd --system nikaai && \
    useradd --system --gid nikaai --create-home --home-dir /home/nikaai nikaai

# Copy project source (owned by nikaai)
COPY --chown=nikaai:nikaai . .

# Create required runtime directories with correct ownership
RUN mkdir -p \
    static/uploads \
    logs \
    app/models \
    app/models/registry && \
    chown -R nikaai:nikaai /app

USER nikaai

EXPOSE 8000

# Healthcheck — start_period allows YOLO model to load + warmup
HEALTHCHECK --interval=30s \
        --timeout=10s \
        --start-period=60s \
        --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start FastAPI via Gunicorn + UvicornWorker.
# Gunicorn forks worker processes BEFORE PyTorch/YOLO are imported, which
# avoids CUDA context corruption and thread-lock deadlocks that occur when
# forking after torch initialisation.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--log-level", "info"]
