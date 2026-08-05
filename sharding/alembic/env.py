import os
from logging.config import fileConfig
from dotenv import load_dotenv
from sqlalchemy import create_engine
from alembic import context
from src.models import Base
from src.database import SHARD_URLS, TOTAL_SHARDS

load_dotenv()

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    """Executes schema migrations across all configured physical database shard nodes."""
    for idx, shard_url in enumerate(SHARD_URLS):
        print(f"[Alembic Cluster Engine] Applying migrations to Shard Node {idx}/{TOTAL_SHARDS - 1} ({shard_url})...")
        connectable = create_engine(shard_url)

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

        connectable.dispose()
        print(f"[Alembic Cluster Engine] Successfully migrated Shard Node {idx}!")


if context.is_offline_mode():
    raise NotImplementedError("Offline mode not supported for multi-shard setups.")
else:
    run_migrations_online()
