# REST API Reference Documentation

Complete endpoint documentation for the Propel AI Fault Detection and Management System.

**Base URL**: `http://localhost:5000/api/v1`

---

## Table of Contents
1. [Health Endpoint](#1-health-endpoint)
2. [Pole Registry APIs](#2-pole-registry-apis)
3. [Telemetry Ingestion APIs](#3-telemetry-ingestion-apis)
4. [Network Graph APIs](#4-network-graph-apis)
5. [Fault Localization APIs](#5-fault-localization-apis)
6. [Repair Ticket APIs](#6-repair-ticket-apis)
7. [Simulator APIs](#7-simulator-apis)
8. [Analytics APIs](#8-analytics-apis)

---

## 1. Health Endpoint

### GET `/health`
Returns system health, database connection status, and active graph node counts.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_poles": 847,
  "active_devices": 765,
  "timestamp": "2026-07-31T11:00:00Z"
}
```

---

## 2. Pole Registry APIs

### GET `/pole-registry/poles`
Returns paginated list of poles with search and filtering.

**Query Parameters**:
- `page` (default: 1)
- `page_size` (default: 20)
- `search` (optional)
- `feeder_id` / `transformer_id` (optional)

**Response (200 OK)**:
```json
{
  "poles": [
    {
      "id": "c1f7b0a8-...",
      "pole_code": "POL-NORTH-01-002",
      "feeder_code": "FDR-HYD-NORTH-01",
      "transformer_code": "TRF-NORTH-01",
      "seq_on_line": 2,
      "device_id": "DEV-MAC-00-002",
      "energized": true
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 847,
    "total_pages": 43
  }
}
```

### POST `/pole-registry/import`
Imports poles from a CSV file upload.

**Response (200 OK)**:
```json
{
  "status": "success",
  "imported_count": 847,
  "errors": []
}
```

---

## 3. Telemetry Ingestion APIs

### POST `/telemetry`
Ingests a single IoT sensor telemetry payload.

**Request Payload**:
```json
{
  "device_id": "DEV-MAC-00-002",
  "pole_id": "POL-NORTH-01-002",
  "event": "power_lost",
  "energized": false,
  "ts": "2026-07-31T11:00:00Z",
  "seq": 105,
  "battery_mv": 3720,
  "rssi": -78,
  "fw": "1.4.2"
}
```

**Response (201 Created)**:
```json
{
  "status": "success",
  "message": "Telemetry event ingested.",
  "telemetry_id": "d98e72...",
  "out_of_order": false
}
```

### POST `/telemetry/bulk`
Ingests array of telemetry events in bulk.

---

## 4. Network Graph APIs

### GET `/network/tree`
Returns complete network graph topology hierarchy.

### GET `/network/poles/:code`
Returns metadata and power status for a specific pole node.

---

## 5. Fault Localization APIs

### GET `/faults/analyze`
Triggers deterministic fault localization analysis across the network graph.

**Response (200 OK)**:
```json
{
  "summary": {
    "total_incidents": 1,
    "span_faults": 1,
    "sensor_anomalies": 0,
    "analyzed_at": "2026-07-31T11:00:00Z"
  },
  "incidents": [
    {
      "incident_id": "INC-SPAN-0001",
      "fault_type": "SPAN_FAULT",
      "upstream_pole": "POL-NORTH-01-001",
      "downstream_pole": "POL-NORTH-01-002",
      "confidence": 100,
      "estimated_households": 45,
      "reason": "Upstream pole POL-NORTH-01-001 is ENERGIZED, but downstream pole POL-NORTH-01-002 is DE-ENERGIZED."
    }
  ]
}
```

---

## 6. Repair Ticket APIs

### GET `/tickets`
Returns paginated repair tickets list.

### PUT `/tickets/:id/status`
Updates ticket status lifecycle state.

**Request Payload**:
```json
{
  "status": "ACKNOWLEDGED",
  "assigned_engineer": "John Doe",
  "assigned_team": "Alpha Response Crew"
}
```

### POST `/tickets/:id/auto-verify`
Auto-verifies a `RESOLVED` ticket against live telemetry power restoration.

---

## 7. Simulator APIs

### GET `/simulator/scenarios`
Returns list of preset scenario cards.

### POST `/simulator/run`
Executes a synthetic outage scenario.

**Request Payload**:
```json
{
  "scenario_id": "small_span_fault",
  "pole_id": "POL-NORTH-01-002"
}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "fault_localization": { ... },
  "tickets_created": [ ... ],
  "ticket_numbers": ["TKT-2026-0001"],
  "ticket_count": 1
}
```

---

## 8. Analytics APIs

### GET `/analytics/overview`
Returns system KPIs and network health percentage.

### GET `/analytics/reliability`
Returns MTTR (minutes), availability %, and outage size metrics.

### GET `/analytics/export/:dataset?format=csv|json`
Exports dataset (`faults`, `tickets`, `simulator`) as downloadable CSV or JSON file.
