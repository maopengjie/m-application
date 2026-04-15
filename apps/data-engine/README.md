# Data Engine

## Local infrastructure

Start MySQL 8 and Redis:

```bash
docker compose -f apps/data-engine/docker-compose.yml up -d mysql redis
```

If Docker is unavailable, use the local MySQL 8.4 helper script and Homebrew Redis:

```bash
zsh apps/data-engine/scripts/start-mysql84.sh
brew services start redis
```

Start Elasticsearch only when you need product search indexing:

```bash
docker compose -f apps/data-engine/docker-compose.yml --profile search up -d elasticsearch
```

Then enable it in `.env`:

```env
DATA_ENGINE_ENABLE_ELASTICSEARCH="true"
DATA_ENGINE_ELASTICSEARCH_URL="http://127.0.0.1:9200"
```

## Environment

Copy the example environment file and adjust it for your machine:

```bash
cp apps/data-engine/.env.example apps/data-engine/.env
```

Recommended local values:

```env
DATA_ENGINE_MYSQL_DSN="mysql+pymysql://app:app123456@127.0.0.1:3306/m_application?charset=utf8mb4"
DATA_ENGINE_REDIS_URL="redis://127.0.0.1:6379/0"
DATA_ENGINE_ENABLE_ELASTICSEARCH="false"
DATA_ENGINE_ELASTICSEARCH_URL="http://127.0.0.1:9200"
```

## Migrations

Run migrations after MySQL is ready:

```bash
cd apps/data-engine
alembic upgrade head
```

Run the full local data-layer verification:

```bash
zsh apps/data-engine/scripts/verify-data-layer.sh
```

Search integration notes:

- `POST /api/prices/search` uses Elasticsearch when `DATA_ENGINE_ENABLE_ELASTICSEARCH=true`.
- Creating or refreshing `price_monitors` will also sync documents into the `price_monitors` index.
- When Elasticsearch is disabled, the search endpoint returns a clear disabled response instead of failing.

## What is considered complete

- MySQL 8 is complete when the app uses a MySQL DSN and `alembic upgrade head` succeeds.
- Redis is complete when the app can read and write cache entries against a running Redis instance.
- Elasticsearch is optional until search scale requires it. Keep `DATA_ENGINE_ENABLE_ELASTICSEARCH=false` until then.
