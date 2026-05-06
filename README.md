<div align="center">
  <img alt="M-Application Logo" width="200" src="./apps/web-ele/public/logo.png">
  <h1>M-Application</h1>
  <p>A personal, high-performance web application base.</p>
</div>

## Introduction

**M-Application** is a personal project built on top of a modern technology stack. It provides a robust architecture for developing advanced web applications with a focus on intelligence, performance, and premium user experience.

## Technology Stack

- **Frontend**: Vue 3, Vite, TypeScript
- **UI Components**: Element Plus, Shadcn UI
- **State Management**: Pinia
- **Styling**: Tailwind CSS
- **Iconography**: Lucide Vue Next, Iconify

## Getting Started

### Prerequisites

- Node.js >= 20.x
- pnpm >= 10.x

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pnpm install
   ```

### Development

Run the development server for the main application:
```bash
pnpm dev
```

### Data Center Workers

The data-center backend uses Redis + Celery for scraping and maintenance jobs.
`docker-compose.yml` starts:

- `worker`: executes scrape tasks.
- `worker-beat`: schedules recurring jobs.

Recommended Docker workflow:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f backend worker worker-beat
```

Recommended verification workflow:

```bash
pnpm run ci:data-center
```

For a running Docker stack, you can also run the backend E2E smoke test inside the backend container:

```bash
docker compose cp scripts/verify_data_center_e2e.py backend:/tmp/verify_data_center_e2e.py
docker compose exec -T backend python /tmp/verify_data_center_e2e.py --base-url http://127.0.0.1:8000
```

Useful environment switches:

- `ENABLE_DEMO_SEED=false`: keep demo data disabled in production.
- `ENABLE_PERIODIC_SCRAPE=true`: periodically refresh active product prices.
- `PERIODIC_SCRAPE_INTERVAL_MINUTES=30`: active product scrape interval.
- `PERIODIC_SCRAPE_LIMIT=20`: max products per scheduled scrape batch.
- `PERIODIC_SCRAPE_PLATFORM=jd`: optional platform filter.
- `MAINTENANCE_INTERVAL_MINUTES=5`: stale task cleanup interval.
- `ENABLE_PERIODIC_CATEGORY_SYNC=true`: periodically refresh the JD category tree.
- `PERIODIC_CATEGORY_SYNC_HOURS=24`: category tree sync interval.

Production notes:

- Set a non-default `POSTGRES_PASSWORD` before first boot.
- Keep `ENABLE_DEMO_SEED=false` unless you intentionally want sample data.
- Start `worker-beat` only once per deployment to avoid duplicate scheduled scrape batches.
- Use the SKU repository scrape overview page to confirm schedule status, open task count, and recent failures.
- Real marketplace scraping depends on external network, DNS, anti-bot behavior, and page selector stability; failed or low-quality scrapes are surfaced in the data-cleaning anomaly queue.

### Build

Build the production version:
```bash
pnpm build:web
```

## Features

- **Personalized Branding**: Fully customized logo, colors, and metadata.
- **Monorepo Structure**: Clean separation of core logic, UI kits, and application code.
- **Advanced UI**: Premium designs with smooth transitions and modern aesthetics.
- **Integrated Analytics**: Tools for monitoring and market intelligence.

## License

[MIT](./LICENSE) © 2026 maopengjie
