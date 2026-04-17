# Decidely Platform - Deployment & Demo Guide

This guide provides a minimal set of instructions to get the full-stack platform (Frontend + Backend) running for demonstration purposes.

## 1. Prerequisites
- **Node.js**: v18+ & **pnpm**: v8+
- **Python**: v3.11+
- **Docker**: For MySQL and Redis

---

## 2. Infrastructure & Backend Setup (Data Engine)

The backend handles price crawling, analysis, and API services.

```bash
cd apps/data-engine

# 1. One-click setup (starts Docker, runs migrations, seeds data)
chmod +x setup.sh
./setup.sh

# 2. Start the Backend server
.venv/bin/python src/main.py
```
*Backend runs at: `http://127.0.0.1:8000`*

---

## 3. Frontend Setup (Web-Ele)

The frontend is built on Vben Admin (Vue 3 + Element Plus).

```bash
cd apps/web-ele

# 1. Install dependencies
pnpm install

# 2. Start the Dev server
pnpm run dev
```
*Frontend runs at: `http://127.0.0.1:5777`*

---

## 4. Demo Accounts & Access

| Username | Password | Role | Features |
| :--- | :--- | :--- | :--- |
| **vben** | `123456` | `super` | Full system access (including Task Monitor) |
| **admin** | `123456` | `admin` | Operations (Price Update, Risk Analysis) |
| **jack** | `123456` | `user` | Standard User (Search, Detail, Alerts) |

---

## 5. Key Demo Flow

1. **Login**: Use `vben` for the full experience.
2. **Search**: Search for "iPhone" in top search bar or homepage.
3. **Detail**: Click a product card to see the **Price Trend Chart** and **Competition Table**.
4. **Analysis**: Check the **Decision Card** (AI buy recommendation) and **Risk Panel**.
5. **Alert**: Click "降价提醒" to create a monitor.
6. **Task**: Navigate to `工具 -> 爬虫任务` to see background engine status.
7. **Coupon**: Navigate to `优惠计算` to see aggregated platform coupons.

---

## 6. Troubleshooting
- **API 404/500**: Ensure the backend is running and you ran `./setup.sh` to initialize the database.
- **Frontend Build**: If `pnpm run build` fails, ensure you have the correct shadcn dependencies (already patched).
- **Docker**: If `setup.sh` hangs on MySQL wait, ensure Docker Desktop is running.
