FROM postgres:16-alpine

# Copy the initialization script
COPY init-db.sh /docker-entrypoint-initdb.d/

# Enable pg_stat_statements in the config
RUN echo "shared_preload_libraries = 'pg_stat_statements'" >> /usr/local/share/postgresql/postgresql.conf.sample
RUN echo "pg_stat_statements.track = all" >> /usr/local/share/postgresql/postgresql.conf.sample
