#!/bin/sh
set -e

# Execute database schema creation & seeding ONCE before spawning Gunicorn worker processes
echo "[ENTRYPOINT] Initializing database schema and data..."
python -c "
from app import create_app
from app.database.init_db import seed_database_if_empty
app = create_app()
seed_database_if_empty(app)
"

echo "[ENTRYPOINT] Starting web server..."
exec "$@"
