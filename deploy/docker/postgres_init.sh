#!/bin/sh
set -eu

create_db_if_not_exists() {
  db="$1"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" \
       -v db="$db" -v owner="$POSTGRES_USER" <<-'EOSQL'
    SELECT format('CREATE DATABASE %I', :'db')
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db')\gexec
    GRANT ALL PRIVILEGES ON DATABASE :"db" TO :"owner";
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
    create_db_if_not_exists "$db"
  done
fi
