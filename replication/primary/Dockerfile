FROM postgres:latest

COPY init-replication.sh /docker-entrypoint-initdb.d/

CMD ["postgres", \
     "-c", "wal_level=replica", \
     "-c", "max_wal_senders=10", \
     "-c", "max_replication_slots=10", \
     "-c", "hot_standby=on"]
