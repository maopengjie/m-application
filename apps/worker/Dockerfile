FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright and Postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY apps/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY apps/worker /app

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
