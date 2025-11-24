#!/bin/bash
# Script to create initial database migration

cd /app
alembic revision --autogenerate -m "Initial schema"
