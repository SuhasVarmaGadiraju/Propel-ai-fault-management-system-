# AI Assistance & Engineering Workflow Log

This document describes how AI tools were integrated into the development process of the Propel AI Fault Detection and Management System. It outlines where AI generated useful code, where AI recommendations were rejected or modified, manual engineering efforts, and prompt examples.

---

## AI Assistance Overview & Estimation

- **Estimated AI-Assisted Portion**: ~65%
- **Estimated Manual Engineering & System Design Portion**: ~35%
- **AI Tools Used**: Antigravity AI Assistant (Gemini 3.6 Flash / Claude 3.5 Sonnet engine), GitHub Copilot

---

## Where AI Helped Accelerate Development

AI assistance was particularly effective in generating boilerplate code, unit test suites, and frontend component structures:

1. **Boilerplate CRUD & Route Handlers**: Rapidly generating Flask Blueprint boilerplate routes, SQLAlchemy ORM models (`Feeder`, `Transformer`, `Pole`, `Device`, `Telemetry`, `Ticket`), and Pydantic/marshmallow schema validators.
2. **Pytest Test Suites**: Writing unit test fixtures and assertions across 43 test cases in `backend/app/tests/` (testing missing CSV headers, sequence lag markers, ticket state machine transitions, and statistics APIs).
3. **Tailwind CSS React Layouts**: Generating responsive React card layouts, modal dialogs, status badges, and table views matching modern utility dashboard aesthetics.
4. **Data Generation Scripts**: Generating realistic database seed data scripts (`scripts/seed_database.py`) to create 3 Feeders, 15 Transformers, ~850 Poles, and ~750 IoT devices with realistic GPS coordinates and parent-child radial chains.

---

## Prompt Examples Used During Development

### Prompt 1: Telemetry Deduplication & Sequence Tagging
> *"Write a Python service method `process_telemetry` that takes a dictionary payload containing `device_id`, `sequence_number`, `voltage_v`, `current_a`, and `energized`. Check if the `(device_id, sequence_number)` pair already exists in the database. If it exists, return `duplicate_ignored = True`. If not, check if `sequence_number` is less than `device.last_sequence`. If it is less, flag `out_of_order = True` and save the telemetry record."*

### Prompt 2: Deterministic Span Outage Algorithm
> *"Create a graph boundary detection algorithm in Python that iterates through an in-memory tree of electrical poles. If a parent pole is energized (`energized = True`) and its child pole is dark (`energized = False`), record a `SPAN_FAULT` incident between the parent and child pole codes. Add a check to suppress false alarms if any downstream child of a dark pole is actually energized."*

### Prompt 3: React Settings & Administration Dashboard
> *"Create a React page component `SystemSettings.jsx` using Tailwind CSS and `react-icons/fi`. Include sections for read-only system info, configurable fault thresholds stored in local state, notification toggles, a table listing REST API endpoints with copy buttons, analytics stat cards, export buttons, and system metadata."*

---

## Where AI Suggestions Were Rejected or Corrected

AI tools frequently proposed incorrect, inefficient, or non-deterministic solutions that required manual intervention and engineering corrections.

### Case 1: Attempted Use of Non-Deterministic LLMs for Fault Localization

#### AI Initial Suggestion
The AI initially suggested sending raw telemetry logs to an external OpenAI / Gemini LLM API prompt to parse and guess line break locations.

#### Why It Was Rejected
Utility grid operations require strict deterministic guarantees. Relying on an external LLM API introduced:
- Non-deterministic outputs (different diagnoses for identical telemetry inputs).
- High API latency (800ms – 2500ms per check vs. < 5ms requirement).
- Risk of hallucinations during multi-span outages.

#### Correction
The LLM suggestion was rejected. Instead, we wrote a deterministic graph boundary search algorithm (`FaultLocalizationService`) that scans in-memory tree pointers in $O(V + E)$ time with mathematical confidence formulas.

---

### Case 2: Incomplete N+1 Query Logic in CSV Pole Registry Import

#### AI Initial Suggestion
When writing `PoleRegistryImportService.import_csv()`, the AI generated code that queried the database inside a `for` loop for every row in the CSV file:

```python
# REJECTED AI CODE: Caused N+1 database queries
for row in reader:
    feeder = Feeder.query.filter_by(feeder_code=row["feeder_id"]).first()
    transformer = Transformer.query.filter_by(transformer_code=row["dt_id"]).first()
    pole = Pole.query.filter_by(pole_code=row["pole_id"]).first()
    # ... insert pole ...
```

#### Why It Was Identified & Corrected
Importing a sample CSV containing 800+ pole records took over 12 seconds due to thousands of individual SQL queries (`800 * 3 = 2,400 database round-trips`).

#### Correction
Replaced the loop queries with an in-memory dictionary cache built before processing rows:

```python
# MANUAL CORRECTION: Pre-cache entities in dictionaries for O(1) lookups
feeders_by_code = {f.feeder_code: f for f in Feeder.query.all()}
trfs_by_code = {t.transformer_code: t for t in Transformer.query.all()}
poles_by_code = {p.pole_code: p for p in Pole.query.all()}

for row in reader:
    feeder = feeders_by_code.get(row["feeder_id"])
    transformer = trfs_by_code.get(row["dt_id"])
    existing_pole = poles_by_code.get(row["pole_id"])
    # ... process in memory ...
```

This reduced the 800-record CSV import execution time from 12.4 seconds to **0.18 seconds**.

---

### Case 3: Invalid State Machine Transitions in Repair Tickets

#### AI Initial Suggestion
The AI generated a generic ticket update endpoint that allowed updating a ticket's `status` column directly to any string value without validation.

#### Why It Was Identified & Corrected
Technicians could skip critical operational steps (e.g., jumping directly from `NEW` to `CLOSED` without going through `ASSIGNED` or `RESOLVED`).

#### Correction
Implemented a strict explicit state machine dictionary (`VALID_TRANSITIONS`) in `TicketService`:

```python
VALID_TRANSITIONS = {
    TicketStatus.NEW: [TicketStatus.ACKNOWLEDGED, TicketStatus.CANCELLED],
    TicketStatus.ACKNOWLEDGED: [TicketStatus.ASSIGNED, TicketStatus.CANCELLED],
    TicketStatus.ASSIGNED: [TicketStatus.RESOLVED, TicketStatus.CANCELLED],
    TicketStatus.RESOLVED: [TicketStatus.VERIFIED, TicketStatus.ASSIGNED],
    TicketStatus.VERIFIED: [TicketStatus.CLOSED],
    TicketStatus.CLOSED: [],
}
```

---

## Manual Engineering Highlights

The following core components required hands-on manual software engineering and architectural design:

1. **Domain Model Design**: Modeling self-referencing parent-child pole structures (`parent_pole_id`) to accurately represent radial electrical distribution networks.
2. **In-Memory Graph Engine (`NetworkGraphService`)**: Designing the bi-directional tree dictionary, node lookup hashes, and subtree traversal logic.
3. **Sensor Anomaly Suppression Logic**: Writing logic to suppress false alarm line breaks when dark parent poles have downstream energized child poles.
4. **State Machine Verification**: Linking live graph telemetry restoration checks directly to automated ticket verification (`auto-verify`).
5. **Docker Compose Orchestration**: Writing production multi-container dependency orchestration (`pg_isready` health checks, volume bindings, Nginx static proxying).
