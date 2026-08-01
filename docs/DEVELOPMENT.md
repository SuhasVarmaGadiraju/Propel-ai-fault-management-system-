# Developer Quickstart & Testing Guide

This guide provides instructions for developers working on the Propel AI Fault Detection and Management System.

---

## 1. Local Environment Setup

### Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Python Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
```

---

## 2. Running Pytest Unit Test Suite

The test suite covers models, graph topology, telemetry ingestion, fault localization, repair tickets, simulator scenarios, and analytics endpoints.

```bash
python -m pytest backend/app/tests/
```

Expected Output:
```
============================= 43 passed in 1.38s ==============================
```

---

## 3. Database Seeding & Scripts

### Reset Database
```bash
python scripts/reset_database.py
```

### Re-Import Pole Registry
```bash
python scripts/import_poles.py
```

### Generate Telemetry Events
```bash
python scripts/generate_telemetry.py
```
