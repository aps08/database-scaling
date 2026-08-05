# Production Multi-Shard Database Migration Guide

This document outlines the essential operational steps and strategy for executing zero-downtime database schema migrations across a **4-Shard PostgreSQL Cluster** powering a **FastAPI application**.

## Zero-Downtime Migration Principles

In a multi-shard cluster, standard single-transaction DDL is impossible because PostgreSQL does not support 2-Phase Commit (2PC) for schema modifications across independent physical database servers.

To prevent schema drift and avoid downtime, migrations follow a backward-compatible **Expand and Contract** strategy:

- **Phase 1: Expand (Non-Breaking Schema Changes):** Apply non-breaking DDL across all physical database shard nodes. Existing live application servers ignore the new structure and continue serving user traffic normally.
- **Phase 2: Application Code Deployment:** Deploy updated application services configured to utilize the expanded database schema fields.
- **Phase 3: Contract (Cleanup Phase):** Once all application instances are updated and verified, remove legacy columns or temporary dual-writing triggers across all shards if necessary.

## Real-World Production Migration Workflow Example

### Example Scenario: Adding an Optional `age` Column to `users` Table

- **Step 1: Apply Idempotent DDL Across All Database Shards:** Execute schema migrations targeting each database shard node independently. Use strict connection lock timeouts to prevent migration tasks from waiting on exclusive locks and blocking live application queries:
  ```sql
  -- Set short lock timeout to avoid blocking live connections
  SET lock_timeout = '3000ms';

  -- Idempotent Column Creation (Safe to retry if interrupted)
  ALTER TABLE users ADD COLUMN IF NOT EXISTS age INT DEFAULT NULL;

  -- Non-blocking Concurrent Index Creation
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_age ON users(age);
  ```
- **Step 2: Track Per-Shard Migration State:** Record successful DDL executions per shard in a centralized migration state store. If a single shard fails due to a lock timeout, halt further steps and alert engineering without disrupting active application instances.
- **Step 3: Deploy Application Code (FastAPI v2):** Deploy updated application services containing updated Pydantic models and SQLAlchemy schemas to read and write the new column.
- **Step 4: Verify System Health:** Monitor API error metrics and database connection pools across all shard nodes to ensure complete operational stability.

## Production Deployment Checklist

- **Pre-Flight Health Checks:** Verify CPU/memory utilization is below 60% and confirm zero long-running blocking transactions across all physical database shards.
- **Execute Non-Breaking DDL:** Apply DDL additions with configured lock timeouts across all physical database shard instances.
- **Deploy Application Services:** Perform rolling deployments of updated FastAPI web applications configured with updated schemas.
- **Post-Deployment Smoke Test:** Run validation endpoints across all shard nodes and inspect error log telemetry.

