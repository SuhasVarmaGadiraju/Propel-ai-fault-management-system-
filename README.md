# Propel AI Fault Detection & Management System

Production-quality AI Fault Detection and Management System for radial power distribution networks.

## Architecture & Infrastructure Overview

The system consists of three containerized services managed via Docker Compose:
- **PostgreSQL 16 Database**: Persistent database service on port `5432` with automated health checks (`pg_isready`).
- **Flask Backend API**: Python 3.11 Application Factory server running on port `5000` with SQLAlchemy, Flask-Migrate, Flask-CORS, and global error middleware.
- **React (Vite) Frontend**: Enterprise blue & white dashboard running on port `3000` (Nginx container on port `80`) with React Router DOM, Axios client, and component architecture.

---

## Local Development & Docker Deployment

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes `docker compose`)
- [Python 3.10+](https://www.python.org/) *(Optional for local non-Docker development)*
- [Node.js 18+](https://nodejs.org/) *(Optional for local non-Docker development)*

---

### Step 1: Environment Setup

Copy `.env.example` to `.env` at the root directory:

```bash
cp .env.example .env
```

Default environment variables configured in `.env.example`:
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_DB=propel_fault_db`
- `BACKEND_PORT=5000`
- `FRONTEND_PORT=3000`
- `VITE_API_BASE_URL=http://localhost:5000/api/v1`

---

### Step 2: Build & Start Containers

Run Docker Compose to build images, initialize networking, start PostgreSQL, wait for database readiness, and launch backend & frontend services:

```bash
docker compose up --build
```

To run in detached background mode:

```bash
docker compose up --build -d
```

---

### Step 3: Verification & Access Points

Once all services report healthy status:

| Service | Access URL | Description |
| :--- | :--- | :--- |
| **Frontend Dashboard** | `http://localhost:3000` | Enterprise React Dashboard |
| **Backend Health Check** | `http://localhost:5000/api/v1/health` | Backend Health API Endpoint |
| **PostgreSQL Database** | `localhost:5432` | PostgreSQL Database Server |

#### Verify Backend Health API Response:
```bash
curl http://localhost:5000/api/v1/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "service": "Propel Fault Management Backend"
}
```

---

### Managing Containers

- **View Service Status & Health Checks**:
  ```bash
  docker compose ps
  ```

- **View Logs**:
  ```bash
  docker compose logs -f
  ```

- **Stop Services**:
  ```bash
  docker compose down
  ```

- **Stop Services & Reset Persistent Data**:
  ```bash
  docker compose down -v
  ```

---

### Database Migrations (Flask-Migrate)

Flask-Migrate is pre-configured under `backend/migrations/`. When database models are introduced in future development phases, generate and apply migrations as follows:

```bash
# Generate a new migration script
docker compose exec backend flask db migrate -m "Add initial models"

# Apply migrations to PostgreSQL
docker compose exec backend flask db upgrade
```

---

## Project Structure

```
.
├── backend/                  # Flask application factory backend
│   ├── app/                  # Application modules (routes, database, config, middleware)
│   ├── migrations/           # Flask-Migrate database migration scripts
│   ├── Dockerfile            # Multi-stage Python backend image
│   ├── requirements.txt      # Dependencies manifest
│   └── run.py                # Server execution entrypoint
├── frontend/                 # React (Vite) + Tailwind CSS dashboard
│   ├── src/                  # Components, layouts, pages, routes, services
│   ├── Dockerfile            # Multi-stage Nginx distribution image
│   └── package.json          # Dependencies manifest
├── docs/                     # Comprehensive architecture and API documentation
│   ├── ARCHITECTURE.md       # High-level architecture specification
│   ├── API.md                # REST API contract specification
│   ├── DEPLOYMENT.md         # Deployment & container guidelines
│   ├── AI-WORKFLOW.md        # AI telemetry & fault localization workflows
│   ├── DEVELOPMENT.md        # Developer onboarding & coding standards
│   └── ROADMAP.md            # Strategic milestones & task backlog
├── scripts/                  # Utility scripts & maintenance tools
│   ├── seed_database.py      # Database seeding script template
│   ├── import_poles.py       # Grid poles CSV import script template
│   └── reset_database.py     # Database schema wipe & reset tool template
├── data/                     # Data imports, exports, and sample records
│   ├── sample/               # Sample CSV and JSON datasets (poles, telemetry, faults)
│   ├── imports/              # Placeholder for incoming dataset uploads
│   └── exports/              # Placeholder for generated reports
├── docker-compose.yml        # Multi-container orchestration specification
├── .env.example              # Environment variables template
└── README.md                 # Project documentation guide
```

---

## Development Workflow

1. **Branching**: Follow `feature/<feature-name>` or `bugfix/<issue-name>` naming conventions.
2. **Testing**: Run backend pytest suite using `python -m pytest backend/app/tests/`.
3. **Utility Tools**: Utilize CLI tools in `scripts/` for data import, database resetting, and test seeding.

---

## Documentation

Detailed documentation guides are available in the [`docs/`](./docs) directory:
- [System Architecture](./docs/ARCHITECTURE.md)
- [REST API Reference](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [AI & Fault Detection Workflow](./docs/AI-WORKFLOW.md)
- [Development Guidelines](./docs/DEVELOPMENT.md)
- [Project Roadmap](./docs/ROADMAP.md)

---

## Upcoming Phases

- **Phase 2**: Define ORM database models (Poles, Feeders, Telemetry, Faults, Tickets) and apply initial Alembic migrations.
- **Phase 3**: Implement the radial grid IoT telemetry simulator & ingestion stream.
- **Phase 4**: Develop the AI fault detection and localization algorithm engine.
- **Phase 5**: Wire up the interactive React GIS map dashboard and automated ticket management system.

