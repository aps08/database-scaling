#!/bin/bash
set -e

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Starting pg_basebackup from primary..."
    
    mkdir -p "$PGDATA"
    chmod 700 "$PGDATA"
    
    export PGPASSWORD='replication_password'
    
    until pg_isready -h primary -p 5432 -U replication_user; do
        echo "Waiting for primary database to be available..."
        sleep 2
    done

    pg_basebackup -h primary -D "$PGDATA" -U replication_user -vP -X stream -R

    touch "$PGDATA/standby.signal"
    
    echo "Replica initialized from primary."
fi

chown -R postgres:postgres "$PGDATA"

exec gosu postgres "$@"
