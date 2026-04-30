# Decidely Deployment & Setup Guide

This guide ensures a stable and consistent setup for the Decidely platform across different environments.

## 1. Prerequisites

- **Python 3.13+**
- **Node.js 20+** (pnpm recommended)
- **MySQL 8.0**
- **Redis**

## 2. Backend (Data Engine) Setup

```bash
cd apps/data-engine

# 1. Create Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Environment Configuration
cp .env.example .env
# Edit .env with your MySQL and Redis credentials
# Important: Ensure DATA_ENGINE_MYSQL_DSN is correct

# 4. Initialize Database (Creates DB, Migrations, Seed Data)
python scripts/init_db.py

# 5. Run Application
python src/main.py
```

## 3. Frontend (Web-Ele) Setup

```bash
cd apps/web-ele

# 1. Install Dependencies
pnpm install

# 2. Run Development Server
pnpm dev
```

## 4. Troubleshooting

- **DB Connection Error**: Verify that MySQL is running and the port in `.env` matches.
- **Vite Proxy Error**: Ensure the backend is running on `http://localhost:8000`.
- **Redis Connection**: Decidely uses Redis for caching and task scheduling; ensure it's running.

## 5. Production Notes

- Use `gunicorn` with `uvicorn` workers for the backend.
- Build the frontend using `pnpm build`.
- Use a persistent volume for SQLite if not using MySQL.
