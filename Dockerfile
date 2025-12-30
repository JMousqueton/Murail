# Multi-stage Dockerfile for Murail Crisis Simulation Platform
# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Add metadata labels
LABEL maintainer="Julien Mousqueton"
LABEL description="Murail - Crisis Exercise Simulation Platform inspired by ANSSI's REMPAR25"
LABEL version="1.0"

# Create non-root user for security
RUN useradd -m -u 1000 murail && \
    mkdir -p /app /app/static/images /app/Sample /app/i18n && \
    chown -R murail:murail /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/murail/.local

# Copy application files
COPY --chown=murail:murail app.py .
COPY --chown=murail:murail requirements.txt .
COPY --chown=murail:murail templates/ templates/
COPY --chown=murail:murail static/ static/
COPY --chown=murail:murail i18n/ i18n/
COPY --chown=murail:murail Sample/ Sample/

# Set environment variables
ENV PATH=/home/murail/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Paris \
    PORT=5000 \
    LANG=fr

# Switch to non-root user
USER murail

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()" || exit 1

# Run the application with Gunicorn for production
CMD ["python", "app.py"]
