# Decidely Platform - Deployment & Maintenance Manual

This manual provides technical details for deploying and maintaining the Decidely platform in production and staging environments.

## 1. Dependency Services

| Service | Version | Purpose | Connectivity Note |
| :--- | :--- | :--- | :--- |
| **MySQL** | 8.0+ | Core relational data, user accounts, price history. | Ensure `utf8mb4` collation. |
| **Redis** | 6.2+ | Distributed Leader Election, Task Locking, Token blacklisting. | Essential for clustered backend. |
| **Elasticsearch** | 7.x/8.x | High-performance full-text search (Optional). | Configured via `ENABLE_ELASTICSEARCH`. |

## 2. Startup Sequence (Cluster/Production)

Follow this order to ensure data integrity and avoid service connection timeouts:

1.  **Infrastructure Initialization**: Start MySQL and Redis containers/services.
2.  **Database Migration**: Run `alembic upgrade head` from the `apps/data-engine` directory.
3.  **Data Seeding (First-time only)**: Run `python scripts/seed_data.py`.
4.  **Backend Cluster**: Starting multiple instances of `src/main.py`. The first instance to acquire the Redis lock will become the `Leader` and handle scheduler tasks.
5.  **Frontend Deployment**: Build the `web-ele` package (`pnpm build`) and serve via Nginx or start the dev server for testing.

## 3. Environment Variables (.env)

Key variables in `apps/data-engine/.env`:

| Variable | Default (Example) | Description |
| :--- | :--- | :--- |
| `DATA_ENGINE_DEBUG` | `false` | Enable detailed error messages in the API. |
| `DATA_ENGINE_ACCESS_TOKEN_SECRET` | (Random Hex) | Used for JWT signing. Must be kept secret. |
| `DATA_ENGINE_MYSQL_DSN` | `mysql+pymysql://...` | Connection string for MySQL. |
| `DATA_ENGINE_REDIS_URL` | `redis://...` | Connection for distributed task management. |
| `DATA_ENGINE_ENABLE_ELASTICSEARCH` | `false` | Toggles DB-based vs ES-based search. |

## 4. Default Accounts (Demo)

| Username | Role | Password | Description |
| :--- | :--- | :--- | :--- |
| **vben** | `super` | `123456` | Full access, system monitoring. |
| **admin** | `admin` | `123456` | Task management, manual triggers. |
| **jack** | `user` | `123456` | End-user features only. |

## 5. Maintenance & Troubleshooting

### Log Locations
-   **Backend**: `apps/data-engine/app.log` (Rotates at 10MB).
-   **Docker**: `docker compose logs -f`

### Health Verification
-   Directly query the health endpoint: `GET /health`.
-   Verify all DB columns are synced: `python scripts/verify_schema.py` (if provided).

### Emergency Rollback
Refer to [ROLLBACK.md](./ROLLBACK.md) for detailed instructions on reverting code and database schema.
