# Engineering Decisions Log

This document records the architectural and design decisions made during the development of the Propel AI Fault Detection and Management System. Each decision outlines the problem context, evaluated alternatives, chosen solution, rationale, trade-offs, and future improvements.

---

## Decision 1: In-Memory Radial Graph Representation vs. Database Traversal

### Problem
Calculating radial tree relationships and traversing downstream poles on every incoming telemetry packet using SQL recursive Common Table Expressions (CTEs) or deep join queries creates high database read latency.

### Alternatives
1. **Database Traversal**: Query `parent_pole_id` recursively in SQL for every fault localization check.
2. **Graph Database**: Introduce a dedicated graph database like Neo4j.
3. **In-Memory Graph Structure (`NetworkGraphService`)**: Build a light, in-memory bi-directional tree dictionary during Flask application startup and update node states dynamically as telemetry arrives.

### Chosen Solution
**In-Memory Graph Structure (`NetworkGraphService`)**.

### Reason
- Offers $O(1)$ node lookup speed by pole code or ID.
- Upstream parent path traversal and downstream child subtree operations complete in under 5 milliseconds.
- Avoids adding complex external infrastructure dependencies like Neo4j for a single 11kV distribution grid domain model.

### Trade-offs
- **Process Memory Footprint**: In-memory nodes reside in application memory.
- **Worker Synchronization**: In multi-worker deployments (e.g. Gunicorn), graph state updates in one worker process are not automatically visible to other workers without an external cache like Redis.

### Future Improvements
Integrate Redis as a shared state cache for multi-worker Flask deployments.

---

## Decision 2: Deterministic Rule Engine vs. Non-Deterministic LLMs for Fault Localization

### Problem
Critical electrical grid operations require predictable, reproducible fault localization. Using generative Large Language Models (LLMs) to infer line breaks introduces non-deterministic outputs, hallucination risks, and latency.

### Alternatives
1. **Generative LLM Prompting**: Send telemetry logs to an LLM prompt to diagnose broken spans.
2. **Machine Learning Classifier**: Train a supervised classification model on historical telemetry data.
3. **Deterministic Boundary Algorithm & Rule-Based Confidence Scoring**: Apply deterministic graph search algorithms to isolate span breaks, substation trips, and feeder outages, using explicit mathematical formulas for confidence scores.

### Chosen Solution
**Deterministic Boundary Algorithm & Rule-Based Confidence Scoring**.

### Reason
- 100% reproducible diagnostic results.
- Boundary algorithms isolate span breaks (`SPAN_FAULT`), substation failures (`TRANSFORMER_FAULT`), and feeder trips (`FEEDER_FAULT`) deterministically.
- Confidence scoring uses explicit deductions (-25% for unknown topology, -15% for sensor gaps, -10% for sequence lag).
- Execution times remain below 5 milliseconds.

### Trade-offs
- Rule-based systems require explicit boundary definitions and cannot automatically learn unprogrammed pattern anomalies without new code rules.

### Future Improvements
Combine deterministic boundary search with anomaly classification for novel telemetry noise patterns.

---

## Decision 3: Dual Database Strategy (SQLite for Development, PostgreSQL for Production)

### Problem
Developers need a fast setup for local testing without launching heavy database containers, but production environments require concurrent write operations and data persistence.

### Alternatives
1. **PostgreSQL Only**: Force developers to run a local PostgreSQL instance or Docker container for local development.
2. **SQLite Only**: Use SQLite for both development and production.
3. **Dual Database Strategy**: Use SQLite by default for standalone local development and PostgreSQL for Docker Compose and production environments.

### Chosen Solution
**Dual Database Strategy**.

### Reason
- Allows new developers to run `python backend/run.py` immediately without Docker or PostgreSQL setup.
- PostgreSQL in Docker Compose handles concurrent database writes and production deployments.
- SQLAlchemy ORM abstracts SQL dialect differences cleanly across both databases.

### Trade-offs
- Minor SQL dialect variations must be tested (e.g. string UUIDs vs native Postgres UUIDs, JSON column types).

### Future Improvements
Maintain Alembic migration files tested against both SQLite and PostgreSQL.

---

## Decision 4: Automated Ticket Restoration Verification via Telemetry Streams

### Problem
In traditional utility operations, repair work orders remain open until a technician manually closes them in the field, leading to stale ticket states even after grid power has been physically restored.

### Alternatives
1. **Manual Verification**: Field technicians manually mark tickets as closed.
2. **Scheduled Polling Job**: Run a background cron job to periodically check and close tickets.
3. **Automated Verification Endpoint (`auto-verify`)**: Expose an endpoint that checks live telemetry across affected span poles when a technician marks a ticket as `RESOLVED`, transitioning it automatically to `VERIFIED`.

### Chosen Solution
**Automated Verification Endpoint (`auto-verify`)**.

### Reason
- Provides instant verification when technicians mark work orders complete.
- Queries live network graph state to verify that 100% of affected span poles report `energized = True`.
- Enforces strict state machine rules (`NEW` → `ACKNOWLEDGED` → `ASSIGNED` → `RESOLVED` → `VERIFIED` → `CLOSED`).

### Trade-offs
- Requires active telemetry transmission from sensors along the restored span.

### Future Improvements
Add automated fallback verification timeouts if sensors fail to transmit immediately after physical line repairs.

---

## Decision 5: Client-Side Local Storage Persistence for Operational Settings

### Problem
Providing operational configuration options (such as confidence thresholds, simulator defaults, and notification preferences) without modifying existing backend algorithms or adding authentication complexity.

### Alternatives
1. **Backend Database Settings Table**: Create new API routes and database tables to persist settings per user session.
2. **Static Read-Only UI**: Render hardcoded, non-interactive configuration lists.
3. **Client-Side `localStorage` Persistence**: Store UI configuration choices locally in React state and `localStorage`, providing immediate interactive feedback without introducing backend changes.

### Chosen Solution
**Client-Side `localStorage` Persistence**.

### Reason
- Fulfills the requirement for an interactive System Settings page without altering backend code or database schemas.
- Keeps settings persistent across browser refreshes for individual operators.
- Provides immediate visual feedback for configuration exports, log downloads, and preference resets.

### Trade-offs
- Settings remain local to the user's browser rather than synchronized across multiple operator workstations.

### Future Improvements
Add multi-user backend configuration synchronization when authentication infrastructure is introduced in future phases.
