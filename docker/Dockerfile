# JCapy Production Docker Image
# Multi-stage build for optimized image size

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml .
COPY src/ ./src/
COPY README.md .
COPY MANIFEST.in .

# Build wheel
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels .

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

# Labels
LABEL maintainer="Irfan Ali <nazrijz336@gmail.com>"
LABEL version="4.1.8"
LABEL description="JCapy - One-Army Orchestrator Daemon"

# Create non-root user for security
RUN useradd -m -s /bin/bash jcapy

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Create necessary directories
RUN mkdir -p /home/jcapy/.jcapy/skills \
    && mkdir -p /app/logs \
    && chown -R jcapy:jcapy /home/jcapy /app

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER jcapy
ENV HOME=/home/jcapy
ENV JCAPY_DAEMON_MODE=1

# Expose ports
# 8080 - Web Control Plane
# 50051 - gRPC (future)
EXPOSE 8080 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Entry point
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["daemon"]