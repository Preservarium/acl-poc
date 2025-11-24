.PHONY: help build start stop restart logs seed clean test status

# Default target
help:
	@echo "ACL PoC - Available Commands"
	@echo "=============================="
	@echo "make build      - Build all Docker images"
	@echo "make start      - Start all services in detached mode"
	@echo "make stop       - Stop all services"
	@echo "make restart    - Restart all services"
	@echo "make logs       - Follow logs from all services"
	@echo "make seed       - Run seed data script"
	@echo "make clean      - Stop services and remove volumes"
	@echo "make test       - Run backend tests"
	@echo "make status     - Show service status"
	@echo "make shell      - Open shell in backend container"

# Build all Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start all services in detached mode
start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Access at http://localhost:8080"

# Stop all services
stop:
	@echo "Stopping services..."
	docker-compose stop

# Restart all services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Follow logs from all services
logs:
	docker-compose logs -f

# Run seed data script
seed:
	@echo "Running seed data script..."
	docker-compose exec backend python seed_data.py

# Stop services and remove volumes (clears database)
clean:
	@echo "Stopping services and removing volumes..."
	docker-compose down -v
	@echo "Cleaned up. All data has been removed."

# Run backend tests (if implemented)
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest

# Show service status
status:
	docker-compose ps

# Open shell in backend container
shell:
	docker-compose exec backend /bin/sh
