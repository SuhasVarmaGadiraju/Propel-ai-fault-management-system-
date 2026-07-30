# REST API Documentation

## Purpose
This document defines the RESTful API contract for the Propel AI Fault Detection and Management System backend. It details endpoint paths, request formats, response schemas, and error codes.

## Table of Contents
1. [Overview & Base URL](#overview--base-url)
2. [Authentication](#authentication)
3. [Health Check Endpoint](#health-check-endpoint)
4. [Electricity Poles Endpoints](#electricity-poles-endpoints)
5. [Telemetry Endpoints](#telemetry-endpoints)
6. [Fault Management Endpoints](#fault-management-endpoints)
7. [Repair Tickets Endpoints](#repair-tickets-endpoints)
8. [Error Handling Standard](#error-handling-standard)

---

## Overview & Base URL
- **Base URL**: `/api/v1`
- **Format**: JSON (`Content-Type: application/json`)

---

## Authentication
*Placeholder: Specifications for API key or JWT token authentication headers.*

---

## Health Check Endpoint

### GET `/api/v1/health`
Returns system operational status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "Propel Fault Management Backend"
}
```

---

## Electricity Poles Endpoints
*Placeholder: `GET /api/v1/poles`, `POST /api/v1/poles`, `GET /api/v1/poles/{id}` endpoint specs.*

---

## Telemetry Endpoints
*Placeholder: `POST /api/v1/telemetry`, `GET /api/v1/telemetry/recent`, `GET /api/v1/poles/{id}/telemetry` endpoint specs.*

---

## Fault Management Endpoints
*Placeholder: `GET /api/v1/faults`, `POST /api/v1/faults/analyze`, `GET /api/v1/faults/{id}` endpoint specs.*

---

## Repair Tickets Endpoints
*Placeholder: `GET /api/v1/tickets`, `POST /api/v1/tickets`, `PATCH /api/v1/tickets/{id}` endpoint specs.*

---

## Error Handling Standard
Standard HTTP error structure:
```json
{
  "error": {
    "code": 404,
    "name": "Not Found",
    "description": "The requested resource was not found."
  }
}
```
