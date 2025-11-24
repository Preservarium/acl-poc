# ACL PoC - Setup Complete

This document provides a quick reference for what has been implemented and how to get started.

## Files Created

### Docker Infrastructure

1. **docker-compose.yml** - Multi-container orchestration
   - nginx: Reverse proxy (port 8080:80)
   - frontend: Vue 3 application
   - backend: FastAPI application
   - Shared data volume for SQLite database

2. **nginx/Dockerfile** - Nginx container
   - Based on nginx:alpine
   - Copies custom configuration

3. **nginx/nginx.conf** - Nginx configuration
   - Routes / to frontend
   - Routes /api/* to backend (strips /api prefix)
   - Proper proxy headers
   - Health check endpoint at /health

### Environment & Configuration

4. **.env.example** - Environment template
   - DATABASE_URL
   - SECRET_KEY
   - ADMIN_USERNAME / ADMIN_PASSWORD
   - Instructions to copy to .env

5. **.gitignore** - Git ignore rules
   - data/ directory
   - __pycache__
   - node_modules
   - .env files
   - Editor files

### Database & Seed Data

6. **backend/seed_data.py** - Database seeding script
   - Creates users: admin, alice, bob, carol
   - Creates groups: ops-team, viewers
   - Creates sites: Factory-1, Factory-2
   - Creates plans: Floor-A, Floor-B
   - Creates sensors: Temp-1, Humidity-1
   - Sets up permissions matching test scenarios
   - Idempotent (can run multiple times safely)

7. **backend/init_db.sh** - Database initialization
   - Auto-creates migration if none exist
   - Runs alembic migrations
   - Runs seed_data.py
   - Called on container startup

### Documentation

8. **README.md** - Comprehensive documentation
   - Architecture diagram
   - Technology stack
   - Quick start guide
   - API documentation with examples
   - Test scenarios explained
   - Permission model details
   - Development guide
   - Troubleshooting tips

9. **Makefile** - Common operations
   - make build - Build images
   - make start - Start services
   - make stop - Stop services
   - make logs - Follow logs
   - make seed - Re-run seed data
   - make clean - Clean up everything
   - make status - Show service status

### Modified Files

10. **backend/Dockerfile** - Updated to run init_db.sh
    - Creates data directory
    - Runs initialization script on startup

## Quick Start

```bash
# 1. Navigate to project directory
cd /workspace/main/acl-poc

# 2. (Optional) Create .env file
cp .env.example .env

# 3. Build and start
docker-compose up --build

# Or use Makefile
make build
make start

# 4. Access application
# Frontend: http://localhost:8080
# API: http://localhost:8080/api
# API Docs: http://localhost:8080/api/docs
```

## Default Login

- Username: `admin`
- Password: `admin123`

## Test Users

| Username | Password   | Groups         |
|----------|------------|----------------|
| admin    | admin123   | -              |
| alice    | alice123   | -              |
| bob      | bob123     | ops-team       |
| carol    | carol123   | ops-team, viewers |

## Seed Data Structure

```
Sites:
├─ Factory-1
│  ├─ Floor-A (Plan)
│  │  ├─ Temp-1 (Sensor)
│  │  └─ Humidity-1 (Sensor)
│  └─ Floor-B (Plan)
└─ Factory-2

Permissions:
├─ admin → Factory-1 → manage (inherit)
├─ admin → Factory-2 → manage (inherit)
├─ alice → Factory-1 → read (inherit)
└─ ops-team → Floor-A → write (inherit)
```

## Verification Steps

After starting the services, verify:

1. **Services are running**:
   ```bash
   docker-compose ps
   # or
   make status
   ```

2. **Check logs for errors**:
   ```bash
   docker-compose logs backend
   ```

3. **Access health endpoint**:
   ```bash
   curl http://localhost:8080/health
   ```

4. **Test login**:
   ```bash
   curl -X POST http://localhost:8080/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   ```

5. **Check seed data created**:
   ```bash
   # Should see: "Seed data created successfully!"
   docker-compose logs backend | grep "Seed data"
   ```

## Test Scenarios

The seed data supports these test scenarios from the spec:

### Scenario 1: Inheritance
- alice has manage on Factory-1 (inherit=true)
- Can create plans and sensors under Factory-1
- Permissions inherit down the tree

### Scenario 2: Deny Override
- Set up alice with read on Factory-1
- Add explicit deny on Floor-B
- Deny takes precedence over inherited allow

### Scenario 3: Group Permissions
- ops-team has write on Floor-A
- bob (member of ops-team) can write to Floor-A
- Permissions work via group membership

### Scenario 4: Creator Auto-Manage
- When a user creates a resource, they automatically get manage permission
- They can then grant/revoke permissions on that resource

## Troubleshooting

### Port already in use
```bash
# Check what's using port 8080
lsof -i :8080

# Or change port in docker-compose.yml
# "8081:80" instead of "8080:80"
```

### Database locked
```bash
# Stop everything and remove database
docker-compose down
rm -rf data/
docker-compose up --build
```

### Permission denied on data/
```bash
chmod 777 data/
```

### See backend logs
```bash
docker-compose logs -f backend
```

## Next Steps

1. **Test the API**: Use the API documentation at http://localhost:8080/api/docs
2. **Test frontend**: Navigate to http://localhost:8080 and login
3. **Run test scenarios**: Follow the test scenarios in README.md
4. **Customize**: Modify .env file for your environment

## Architecture Notes

- **SQLite**: Simple for PoC, use PostgreSQL for production
- **JWT**: Simple auth, tokens expire after 24 hours
- **Async**: Backend uses async SQLAlchemy for performance
- **Inheritance**: Permissions flow down, not up
- **Auto-grant**: Creators get manage permission automatically

## Support

For issues:
1. Check README.md troubleshooting section
2. Check logs: `docker-compose logs`
3. Verify all services are running: `docker-compose ps`
4. Try clean restart: `make clean && make build && make start`
