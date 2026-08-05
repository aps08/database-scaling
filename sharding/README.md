# Sharding Setup

To learn how to use the files and configurations provided in this directory, please follow the detailed guide in this article:

[Scaling High-Volume Databases: A Complete Guide to Application-Level Database Sharding with FastAPI](https://aps08.medium.com)

### Production Shard Migrations: Reality Check

In simple local prototypes, running a basic loop script like `start.sh` with `alembic upgrade head` applies DDL migrations across all database shards sequentially. Production migrations are never this simple, in real-world enterprise environments serving millions of active users across distributed database clusters, executing migrations in a simple loop introduces severe failure modes:

- Partial Failures & Split-Brain Schema: If Shard 0, 1, and 2 succeed but Shard 3 fails due to a network glitch or lock timeout, your system enters an inconsistent, unrecoverable state.
- No Cross-Node DDL Transactions: PostgreSQL does not support 2-Phase Commit (2PC) for schema modifications across independent physical servers.
- Blocking DDL Locks: Running un-isolated `ALTER TABLE` commands on high-traffic shard servers locks tables, causing connection pool exhaustion and global application outages.

For complete zero-downtime deployment strategies, lock timeout configuration, and partial failure resiliency playbooks, check our dedicated [Production Multi-Shard Database Migration Guide (`MIGRATION.md`)](MIGRATION.md).

### Frequently Asked Interview Questions on Database Sharding

#### What is the difference between Database Partitioning and Database Sharding?

- **Partitioning (Single Database Instance):** Splitting a single large table into smaller physical child tables residing on the **same database server**. The database query planner transparently handles routing.
- **Sharding (Multi-Node / Horizontal Scaling):** Distributing database tables across **multiple independent database servers/nodes**. Requires application-level routing or a distributed coordinator (e.g., Citus, Vitess).

#### What is a Sharding Key and how do you choose it?

A Sharding Key is a column (e.g. `user_id` or `tenant_id`) used by the routing algorithm to determine which physical shard node stores a record. A good sharding key ensures even data distribution and prevents write hotspots across nodes.

#### What is a Scatter-Gather Query?

When a query does not include the sharding key in its filter (e.g., `SELECT * FROM users WHERE country = 'US'`), the application router cannot target a single shard node. It must "scatter" the query to all shard nodes simultaneously, "gather" the responses asynchronously, and merge them at the application layer.

#### Why is Database Sharding considered a "Last Resort"?

Sharding introduces significant architectural and operational complexity: losing multi-shard cross-table ACID transactions, requiring application-level query routing, complex re-sharding procedures when adding new nodes, and hot-key skew where single active shards become bottlenecks. Teams should first exhaust query optimization, indexing, caching, vertical scaling, read replicas, and table partitioning before sharding.

#### How do schema migrations work in a production sharded architecture?

In production, schema migrations must be **backward-compatible (Expand & Contract)**. Non-breaking DDL (such as adding a nullable column) is applied across shard nodes with short `lock_timeout` settings before deploying updated application code. Multi-shard orchestrators track per-shard migration state to handle partial failures safely without causing downtime.
