#!/bin/zsh

set -euo pipefail

MYSQLADMIN_BIN="/opt/homebrew/opt/mysql@8.4/bin/mysqladmin"
SOCKET="/tmp/m_application_mysql84.sock"
PORT="3307"

if nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1; then
  "$MYSQLADMIN_BIN" -h 127.0.0.1 -P "$PORT" -u root shutdown
  echo "MySQL 8.4 stopped on 127.0.0.1:$PORT"
else
  echo "MySQL 8.4 is not running on 127.0.0.1:$PORT"
fi
