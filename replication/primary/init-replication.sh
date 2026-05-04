#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER replication_user WITH REPLICATION PASSWORD 'replication_password';
EOSQL

echo "host replication replication_user 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
