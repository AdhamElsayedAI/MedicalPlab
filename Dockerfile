# Multi-stage production Dockerfile for MedicalPlab Cloud API
FROM python:3.11-slim

# Install system utilities (curl required for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create unprivileged application user for production security
RUN useradd -m -u 1000 appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MEDICALPLAB_RUNTIME_MODE=production \
    PYTHONPATH=/app/src:/app

# Install python dependencies
COPY requirements.txt pyproject.toml README.md ./
RUN grep -v "^-e" requirements.txt > requirements-prod.txt && \
    pip install --no-cache-dir -r requirements-prod.txt && \
    rm requirements-prod.txt

# Copy application source code, schemas, and public-safe data
COPY src/ src/
COPY schemas/ schemas/
COPY Data/ Data/
COPY main.py production_main.py ./

# Install medicalplab package
RUN pip install --no-cache-dir --no-deps -e .

# Fix permissions and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose ports: 8080 (Cloud Run standard), 8000 (local/dev), 7860 (Hugging Face Spaces)
EXPOSE 8080 8000 7860

# Health check monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start Uvicorn gateway bound to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn production_main:app --host 0.0.0.0 --port ${PORT:-8080}"]
