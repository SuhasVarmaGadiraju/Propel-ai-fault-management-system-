# Deployment & Operations Guide

This guide describes how to run, deploy, test, and troubleshoot the Propel AI Fault Detection and Management System across local development and containerized production environments.

---

## Prerequisites

Before starting, ensure your system has:

- **Docker & Docker Compose**: Docker Engine 24.0+ and Docker Compose v2.20+
- **Python Environment**: Python 3.12+ and `pip`
- **Node.js Environment**: Node.js 18.0+ and `npm` 9.0+
- **Database (Local)**: SQLite 3 (included) or PostgreSQL 15+

---

## Environment Variables

Copy `.env.example` to `.env` in the root directory:

```ini
# Flask Application Environment
FLASK_ENV=development
SECRET_KEY=propel-fault-management-super-secret-key
PORT=5000

# Database Configuration (Defaults to SQLite for local development)
DATABASE_URL=sqlite:///dev.db

# PostgreSQL Configuration (Used when running in Docker Compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=propel_fault_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# CORS & Frontend API base configuration
CORS_ORIGINS=*
VITE_API_BASE_URL=http://localhost:5000/api/v1
```

---

## Local Development Setup

### 1. Backend Setup

From the repository root:

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Initialize database and seed initial grid topology
python scripts/seed_database.py

# Start Flask backend server
python backend/run.py
```

The backend server runs at `http://localhost:5000`.

### 2. Frontend Setup

In a separate terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend application runs at `http://localhost:3000`.

---

## Production Deployment with Docker Compose

Docker Compose runs the complete stack with PostgreSQL 16 Alpine, Flask API Gateway, and Vite/Nginx frontend.

### Launch Container Stack

From the repository root:

```bash
# Build and launch all container services in detached mode
docker-compose up --build -d
```

Docker Compose spins up three containers in order:
1. `propel-postgres`: PostgreSQL database with volume persistence (`postgres_data`).
2. `propel-backend`: Flask API server waiting for PostgreSQL container health check.
3. `propel-frontend`: Production Nginx web server serving compiled React static assets.

### Access Running Services

- **Frontend Application**: `http://localhost:3000`
- **Backend API Base**: `http://localhost:5000/api/v1`
- **Health Check Endpoint**: `http://localhost:5000/api/v1/health`

---

## Deployment Verification Steps

Verify that services are running correctly:

### 1. Automated Health Check

Send an HTTP GET request to the health endpoint:

```bash
curl -i http://localhost:5000/api/v1/health
```

Expected HTTP response:

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "service": "Propel Fault Management Backend",
  "status": "healthy"
}
```

### 2. Verify Database Seeding

Query pole registry statistics:

```bash
curl -s http://localhost:5000/api/v1/pole-registry/statistics
```

Expected response contains asset counts:

```json
{
  "poles_without_devices": 73,
  "total_devices": 758,
  "total_feeders": 3,
  "total_poles": 831,
  "total_transformers": 15,
  "unknown_topology_count": 495
}
```

### 3. Run Automated Unit Tests

Run the backend Pytest harness:

```bash
python -m pytest backend/app/tests/
```

All 43 unit tests must pass.

---

## Troubleshooting & Operations

### Container Management Commands

```bash
# View running container status
docker-compose ps

# View backend container logs
docker-compose logs -f backend

# View frontend container logs
docker-compose logs -f frontend

# View database container logs
docker-compose logs -f postgres

# Stop all running containers
docker-compose down
```

### Common Deployment Issues

#### 1. Database Connection Refused (`OperationalError`)
- **Cause**: Backend container started before PostgreSQL finished initializing socket connections.
- **Fix**: The `docker-compose.yml` includes a `service_healthy` condition on `postgres`. If starting manually outside Docker, ensure PostgreSQL is running before starting `run.py`.

#### 2. Port Allocation Conflicts (`port is already allocated`)
- **Cause**: Port 5000, 3000, or 5432 is already occupied by a local process.
- **Fix**: Stop conflicting local processes or update environment variables (`BACKEND_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT`) in `.env`.

#### 3. CORS Network Errors in Browser
- **Cause**: Frontend requesting incorrect backend URL or CORS policy blocking requests.
- **Fix**: Verify `VITE_API_BASE_URL` in `frontend/.env` matches backend IP/port and `CORS_ORIGINS=*` is enabled in backend config.

---

## Database Reset Instructions

To clear existing database records and re-seed clean network topology data:

### Local Development Reset

```bash
# Execute database seed script (automatically drops and re-creates tables)
python scripts/seed_database.py
```

### Docker Production Reset

```bash
# Stop containers and remove persistent volume storage
docker-compose down -v

# Re-launch container stack (triggers database creation & seeding)
docker-compose up --build -d
```
