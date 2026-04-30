# Rollback Plan - Decidely Platform

This guide outlines the emergency procedures for reverting the system to its last known stable state in the event of a critical deployment failure.

## 1. Quick Revert (Standard Response)

If the system is unstable after deployment, execute the following commands in order:

### A. Revert Database Schema

Alembic migrations must be rolled back **before** reverting the application code to ensure DB-Code compatibility.

```bash
cd apps/data-engine
# Rollback the last migration step
.venv/bin/alembic downgrade -1
```

### B. Revert Application Code

To revert code in a production environment, use `git revert` to create a new "undo" commit. This preserves history and is safe for shared branches.

```bash
# Revert the most recent commit
git revert HEAD --no-edit

# OR revert a specific commit range
# git revert -m 1 <COMMIT_HASH>

# Push the revert commit
git push origin main
```

_Note: If using a containerized environment (Docker), the fastest way is often to re-deploy the previous successful image tag._

### C. Revert Configuration

If `.env` was modified, restore it from the backup or `.env.example`.

```bash
cp .env.backup .env
```

---

## 2. Recovery Scenarios

| Failure Scenario            | Resolution Path                                                                                     |
| :-------------------------- | :-------------------------------------------------------------------------------------------------- |
| **"Invalid Column" Errors** | Run `alembic downgrade -1` once or twice until the schema matches the code.                         |
| **Login / Auth Failure**    | Check `.env` for `ACCESS_TOKEN_SECRET` consistency. Revert `.env` if changed.                       |
| **Scheduler Duplication**   | Ensure only ONE instance has the leader lock in Redis. Flush Redis if needed: `redis-cli flushall`. |
| **500 Serialization Error** | Rollback code to the previous version immediately.                                                  |

---

## 3. Post-Rollback Verification

After rolling back, verify the system using the following steps:

1. **Health Check**: `curl http://127.0.0.1:8000/health` (Should return `status: healthy`).
2. **Infrastructure Verification**:
   ```bash
   cd apps/data-engine
   .venv/bin/python scripts/verify_infra.py
   ```
3. **Smoke Test**:
   ```bash
   .venv/bin/python tests/acceptance_e2e.py
   ```

---

## 4. Emergency Contacts & Logs

- **Logs**: Check `apps/data-engine/app.log` for the specific error causing the crash.
- **Docker**: If infrastructure is down, run `docker compose down && docker compose up -d`.
