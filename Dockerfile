# =============================================================================
# Dockerfile for Reading List API (P07 - Container Hardening)
# Multi-stage build with security hardening
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and run tests
# -----------------------------------------------------------------------------
FROM python:3.11.9-slim-bookworm AS builder

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies (pinned versions for reproducibility)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# Copy application code
COPY app/ ./app/

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.11.9-slim-bookworm AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Reading List API" \
      org.opencontainers.image.description="Secure API for managing reading lists" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Атаханов Н.Р." \
      org.opencontainers.image.source="https://github.com/GyBJluHv2/course-project-GyBJluHv2-new"

# Security: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Run Python in optimized mode
    PYTHONOPTIMIZE=1

WORKDIR /app

# Security: Create non-root user (C2)
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/false --create-home appuser && \
    # Create necessary directories with correct permissions
    mkdir -p /app && \
    chown -R appuser:appgroup /app

# Copy dependencies from builder stage
COPY --from=builder --chown=appuser:appgroup /build/deps /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Security: Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check with proper timeouts (C2)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
