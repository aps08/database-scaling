import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

SHARD_0_URL = os.getenv("SHARD_0_URL")
SHARD_1_URL = os.getenv("SHARD_1_URL")
SHARD_2_URL = os.getenv("SHARD_2_URL")
SHARD_3_URL = os.getenv("SHARD_3_URL")

if not all([SHARD_0_URL, SHARD_1_URL, SHARD_2_URL, SHARD_3_URL]):
    raise RuntimeError("Missing required SHARD_0_URL, SHARD_1_URL, SHARD_2_URL, or SHARD_3_URL environment variables in .env")

SHARD_URLS = [SHARD_0_URL, SHARD_1_URL, SHARD_2_URL, SHARD_3_URL]
TOTAL_SHARDS = len(SHARD_URLS)

engines = [create_engine(url, pool_pre_ping=True) for url in SHARD_URLS]
SessionGlobals = [
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
    for engine in engines
]


def get_shard_id(sharding_key: int) -> int:
    """
    Application-level Modulo Hash Router function.
    Calculates physical shard ID in O(1) time complexity.
    """
    return sharding_key % TOTAL_SHARDS


def get_db_session(shard_id: int) -> Session:
    """
    Returns a database Session bound to the target physical shard node.
    """
    if shard_id < 0 or shard_id >= TOTAL_SHARDS:
        raise ValueError(f"Invalid shard_id {shard_id}. Must be between 0 and {TOTAL_SHARDS - 1}")
    return SessionGlobals[shard_id]()


def get_all_db_sessions() -> List[Tuple[int, Session]]:
    """
    Returns sessions for all physical database shard nodes.
    Used for scatter-gather operations across the entire database cluster.
    """
    return [(shard_id, SessionGlobals[shard_id]()) for shard_id in range(TOTAL_SHARDS)]
