# M-Application

A monorepo for the Price Monitoring System.

## Project Structure

- `apps/web-ele`: Vue 3 + Element Plus frontend dashboard.
- `apps/data-engine`: Python FastAPI engine for data crawling and authentication.
- `apps/backend-mock`: Development mock server.

## Getting Started

### Prerequisites

- Node.js (v20+)
- pnpm (v10+)
- Python (v3.10+)

### Installation

```bash
pnpm install
```

### Development

```bash
# Start Python Data Engine
cd apps/data-engine
./venv/bin/python src/main.py

# Start Frontend
pnpm dev
```

## License

MIT
