# M-Application

A monorepo for the Price Monitoring System.

## Project Structure

- `apps/web-ele`: Vue 3 + Element Plus frontend dashboard (Vben Admin structure).
- `apps/data-engine`: Python FastAPI engine for data crawling and authentication.
- `apps/backend-mock`: Development mock server based on Nitro.

## Documentation

- [PRD](./docs/PRD.md): Product Requirements Document.
- [Development Plan](./docs/plan.md): Phase-by-phase implementation roadmap.
- [Technology Stack](./docs/technology.md): Detailed technical specifications.
- [Design System (Stitch)](./docs/DESIGN.md): UI/UX blueprint and mockups.
- [Data Engine API](./docs/api-data-engine.md): API documentation for the Python backend.

## Current Progress

- ✅ **Phase 0**: Project skeleton initialized for both frontend and backend.
- 🚧 **Phase 1**: Backend authentication and mock data analysis implemented.
- 🚧 **Dashboard**: Analytics components development in progress.

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
