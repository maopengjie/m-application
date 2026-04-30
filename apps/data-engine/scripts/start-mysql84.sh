#!/bin/zsh

set -euo pipefail

MYSQL_BIN="/opt/homebrew/opt/mysql@8.4/bin/mysql"
MYSQLD_BIN="/opt/homebrew/opt/mysql@8.4/bin/mysqld"
DATADIR="/tmp/m_application_mysql84"
SOCKET="/tmp/m_application_mysql84.sock"
PID_FILE="/tmp/m_application_mysql84.pid"
PORT="3307"

mkdir -p "$DATADIR"

if [[ ! -f "$DATADIR/auto.cnf" ]]; then
  "$MYSQLD_BIN" --initialize-insecure --datadir="$DATADIR"
fi

if nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
  echo "MySQL 8.4 is already running on 127.0.0.1:$PORT"
else
  "$MYSQLD_BIN" \
    --datadir="$DATADIR" \
    --port="$PORT" \
    --socket="$SOCKET" \
    --pid-file="$PID_FILE" \
    --bind-address=127.0.0.1 \
    >/tmp/m_application_mysql84.log 2>&1 &

  for _ in {1..20}; do
    if nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

"$MYSQL_BIN" -h 127.0.0.1 -P "$PORT" -u root -e \
  "CREATE DATABASE IF NOT EXISTS m_application CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "MySQL 8.4 ready at 127.0.0.1:$PORT"
