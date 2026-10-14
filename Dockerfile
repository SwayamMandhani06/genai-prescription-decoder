# Multi-stage Dockerfile for DawaAI: Explainable Multimodal AI for Handwritten Prescription Understanding
# Stage 1: Build the React/Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production Python Backend Runtime
FROM python:3.11-slim AS backend-runtime

# Install system dependencies: Tesseract OCR (Phase 5 baseline) and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create unprivileged application user for DevSecOps least-privilege runtime
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -d /app -s /sbin/nologin appuser

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy core architecture modules
COPY backend ./backend
COPY ai ./ai
COPY data ./data
COPY --from=frontend-builder /app/dist ./dist

# Create uploads directory for immutable original prescription image preservation and set ownership
RUN mkdir -p /app/backend/uploads/samples && \
    chown -R appuser:appuser /app

# Switch to unprivileged user
USER appuser

# Environment configuration
ENV HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    USE_MOCK_PIPELINE=false

EXPOSE 8000

# Container healthcheck targeting root /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start FastAPI application via production Uvicorn server respecting Render's $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
