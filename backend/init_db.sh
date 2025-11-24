#!/bin/bash
# Database initialization script
# Creates migration if none exist, then runs migrations and seeds data

set -e

echo "Checking for existing migrations..."
if [ -z "$(ls -A /app/alembic/versions)" ]; then
    echo "No migrations found. Creating initial migration..."
    alembic revision --autogenerate -m "Initial schema"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python seed_data.py

echo "Database initialization complete!"
