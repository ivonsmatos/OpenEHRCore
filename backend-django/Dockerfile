# ==============================================================================
# Multi-Stage Docker Build for OpenEHRCore Django Backend
# Sprint 28: DevOps Improvement
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# ------------------------------------------------------------------------------
FROM python:3.11-slim as production

# Labels
LABEL maintainer="OpenEHRCore Team" \
      version="1.0.0" \
      description="OpenEHRCore Django Backend - FHIR EHR System"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    APP_USER=appuser

# Create non-root user for security
RUN groupadd --gid 1000 ${APP_USER} \
    && useradd --uid 1000 --gid ${APP_USER} --shell /bin/bash --create-home ${APP_USER}

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR ${APP_HOME}

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} . .

# Create directories for static and media files
RUN mkdir -p staticfiles mediafiles \
    && chown -R ${APP_USER}:${APP_USER} ${APP_HOME}

# Switch to non-root user
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "core.wsgi:application"]

# ------------------------------------------------------------------------------
# Stage 3: Development - With dev tools
# ------------------------------------------------------------------------------
FROM production as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dev Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-django \
    pytest-cov \
    black \
    flake8 \
    isort \
    ipython

USER ${APP_USER}

# Override command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
