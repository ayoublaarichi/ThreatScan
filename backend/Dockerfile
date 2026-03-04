# ── Backend API Dockerfile ──
FROM python:3.11-slim AS base

# Security: run as non-root
RUN groupadd -r threatscan && useradd -r -g threatscan -d /app -s /sbin/nologin threatscan

WORKDIR /app

# System dependencies for python-magic, pefile, yara, lief
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Own the app directory
RUN chown -R threatscan:threatscan /app

USER threatscan

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
