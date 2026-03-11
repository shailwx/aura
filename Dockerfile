# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a prefix
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY main.py .

# Non-root user for security
RUN adduser --disabled-password --gecos "" aura
USER aura

# Environment — override at runtime or via Kubernetes Secret/ConfigMap
ENV GOOGLE_CLOUD_PROJECT=ai-agent-labs-oslo-26-team-6
ENV GOOGLE_CLOUD_LOCATION=europe-north1
ENV GOOGLE_GENAI_USE_VERTEXAI=1
ENV APP_NAME=aura
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
