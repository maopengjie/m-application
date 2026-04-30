#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT_DIR/.venv/bin/activate"

MYSQL_BIN="/opt/homebrew/opt/mysql@8.4/bin/mysql"
MYSQL_PORT="3307"

echo "Checking Redis..."
redis-cli ping

echo "Checking MySQL 8.4..."
"$MYSQL_BIN" -h 127.0.0.1 -P "$MYSQL_PORT" -u root -e "SELECT VERSION();"

echo "Checking Alembic migration state..."
(
  cd "$ROOT_DIR"
  ./.venv/bin/alembic current
)

echo "Checking application schema..."
"$MYSQL_BIN" -h 127.0.0.1 -P "$MYSQL_PORT" -u root -D m_application -e "SHOW TABLES LIKE 'price_monitors';"

echo "Data layer verification complete."
