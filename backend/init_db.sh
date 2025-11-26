#!/bin/bash
# Database initialization script
# Tables are created by SQLAlchemy's create_all() in main.py
# This script handles migrations (if any) and seeds data

set -e

echo "Checking for existing migrations..."
MIGRATION_FILES=$(find /app/alembic/versions -name "*.py" -not -name "__*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$MIGRATION_FILES" -gt 0 ]; then
    echo "Found $MIGRATION_FILES migration file(s). Running migrations..."
    alembic upgrade head || {
        echo "Migration failed. Database may need manual intervention."
        echo "Continuing with startup..."
    }
else
    echo "No migrations found. Tables will be created by SQLAlchemy create_all()."
fi

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
