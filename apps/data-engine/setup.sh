#!/bin/bash
set -e

# setup.sh: One-click initialization for Vben Data Engine

echo "===== Vben Data Engine Setup ====="

# 1. Start Infrastructure (Docker)
echo "Starting MySQL and Redis via Docker..."
docker compose -f docker-compose.yml up -d mysql redis

echo "Waiting for MySQL to be ready..."
# Simple wait loop for MySQL
MAX_RETRIES=30
RETRY_COUNT=0
set +e
until docker compose exec mysql mysqladmin ping -h"127.0.0.1" --silent; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: MySQL failed to start in time."
        exit 1
    fi
    sleep 2
done
set -e
echo "MySQL is up!"

# 2. Virtual Environment & Dependencies
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# 3. Database Migrations
echo "Running migrations..."
.venv/bin/alembic upgrade head

# 4. Seed Data
echo "Seeding database..."
.venv/bin/python scripts/seed_data.py

# 5. Verify
echo "Verifying installation..."
.venv/bin/python scripts/verify_infra.py

echo "=================================="
echo "Setup Complete!"
echo "Backend is ready at http://127.0.0.1:8000"
echo "You can now run: .venv/bin/python src/main.py"
echo "Demo Accounts:"
echo "  - Super: vben / 123456"
echo "  - Admin: admin / 123456"
echo "=================================="
