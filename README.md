# ACL System PoC

Minimal proof-of-concept demonstrating pure ACL (Access Control List) with hybrid inheritance and creator auto-manage functionality.

## Overview

This PoC implements a hierarchical resource permission system where:
- Resources are organized in a 3-level hierarchy: **Site → Plan → Sensor**
- Permissions can be granted to individual users or groups
- Permissions inherit down the hierarchy (optional per-permission)
- Resource creators automatically receive 'manage' permission
- Explicit deny overrides inherited allow

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐         ┌─────────────────────────────┐  │
│   │             │  :8080  │                             │  │
│   │   NGINX     │────────▶│   Vue Frontend              │  │
│   │  (proxy)    │         │   - Permission UI           │  │
│   │             │         │   - Resource browser        │  │
│   └──────┬──────┘         └─────────────────────────────┘  │
│          │                                                  │
│          │ /api/*                                          │
│          ▼                                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                                                     │  │
│   │   FastAPI Backend                                   │  │
│   │   - Auth (simple JWT)                               │  │
│   │   - Permission Service                              │  │
│   │   - Resource CRUD                                   │  │
│   │                                                     │  │
│   └──────────────────────┬──────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                                                     │  │
│   │   SQLite                                            │  │
│   │   /data/acl_poc.db                                  │  │
│   │                                                     │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Frontend**: Vue 3 + Vite + Pinia + TailwindCSS
- **Backend**: FastAPI + Pydantic v2 + SQLAlchemy 2.0
- **Database**: SQLite (file-based, simple for PoC)
- **Container**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup & Run

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd acl-poc
   ```

2. **Create environment file** (optional - defaults work out of the box):
   ```bash
   cp .env.example .env
   # Edit .env if you want to change default values
   ```

3. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

   Or use the Makefile:
   ```bash
   make build
   make start
   ```

4. **Access the application**:
   - Frontend: http://localhost:8080
   - API Docs: http://localhost:8080/api/docs
   - Health Check: http://localhost:8080/health

### Default Credentials

**Admin Account**:
- Username: `admin`
- Password: `admin123`

**Test Users**:
- alice / alice123
- bob / bob123
- carol / carol123

## Seed Data

The system automatically seeds the following test data on first run:

### Users
- **admin** (is_admin=true) - Full system administrator
- **alice** - Regular user
- **bob** - Regular user, member of ops-team
- **carol** - Regular user, member of ops-team and viewers

### Groups
- **ops-team** - Members: bob, carol
- **viewers** - Members: carol

### Resources
- **Sites**:
  - Factory-1
  - Factory-2
- **Plans** (under Factory-1):
  - Floor-A
  - Floor-B
- **Sensors** (under Floor-A):
  - Temp-1
  - Humidity-1

### Permissions
- admin → Factory-1 → manage (inherit=true)
- admin → Factory-2 → manage (inherit=true)
- alice → Factory-1 → read (inherit=true)
- ops-team → Floor-A → write (inherit=true)

## API Documentation

### Authentication

All API requests (except login) require a JWT token in the Authorization header:

```bash
Authorization: Bearer <token>
```

### Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Example Requests

#### List Sites
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/sites
```

#### Create Plan
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Floor-C", "site_id": "<site-id>"}' \
  http://localhost:8080/api/plans
```

#### Grant Permission
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "grantee_type": "user",
    "grantee_id": "<user-id>",
    "resource_type": "site",
    "resource_id": "<site-id>",
    "permission": "read",
    "inherit": true
  }' \
  http://localhost:8080/api/permissions
```

#### Check Permissions
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "checks": [
      {
        "resource_type": "sensor",
        "resource_id": "<sensor-id>",
        "permission": "read"
      }
    ]
  }' \
  http://localhost:8080/api/permissions/check
```

## Test Scenarios

The seed data supports these key test scenarios:

### Scenario 1: Inheritance

**Setup**: alice has 'manage' on site:Factory-1 (inherit=true)

**Tests**:
- alice creates plan:Floor-A under Factory-1 → ✅ allowed
- alice creates sensor:Temp-1 under Floor-A → ✅ allowed
- alice can read/write/delete Temp-1 → ✅ inherited from site

### Scenario 2: Deny Override

**Setup**:
- alice has 'read' on site:Factory-1 (inherit=true)
- alice has 'deny read' on plan:Floor-B

**Tests**:
- alice can read Factory-1 → ✅
- alice can read Floor-A (under Factory-1) → ✅ inherited
- alice can read Floor-B → ❌ explicit deny
- alice can read sensors under Floor-B → ❌ deny propagates

### Scenario 3: Group Permissions

**Setup**:
- group:ops-team has 'write' on plan:Floor-A (inherit=true)
- bob is member of ops-team

**Tests**:
- bob can write to Floor-A → ✅ via group
- bob can write to sensors under Floor-A → ✅ inherited via group
- bob can write to Factory-1 (parent) → ❌ no upward inheritance

### Scenario 4: Creator Auto-Manage

**Setup**: carol has 'create' on plan:Floor-A

**Tests**:
- carol creates sensor:Humidity-1 → ✅
- carol now has 'manage' on Humidity-1 → ✅ auto-granted
- carol can grant 'read' on Humidity-1 to dave → ✅

## Permission Model

### Permission Types

- **read**: View resource details
- **write**: Modify resource
- **delete**: Delete resource
- **create**: Create child resources
- **manage**: Full control (includes all other permissions + grant/revoke permissions)

### Permission Hierarchy

```
manage
  ├── read
  ├── write
  ├── delete
  ├── create
  └── share (grant/revoke permissions)
```

Having 'manage' implies all other permissions. Having 'write' does NOT imply 'read' - permissions must be checked individually.

### Inheritance

Permissions set on a parent resource can inherit to children if `inherit=true`:
- Site permissions → inherit to Plans and Sensors
- Plan permissions → inherit to Sensors
- Sensor permissions → do not inherit (leaf node)

### Deny Takes Precedence

If a user has both allow and deny for the same permission (either directly or inherited), **deny wins**.

## Development

### Manual Database Seeding

To re-run the seed data script:

```bash
# Via docker-compose
docker-compose exec backend python seed_data.py

# Or via Makefile
make seed
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Or via Makefile
make logs
```

### Stopping Services

```bash
docker-compose down

# Remove volumes (clears database)
docker-compose down -v

# Or via Makefile
make clean
```

### Database Migrations

The backend uses Alembic for database migrations:

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Makefile Commands

```bash
make build     # Build all Docker images
make start     # Start all services in detached mode
make stop      # Stop all services
make restart   # Restart all services
make logs      # Follow logs from all services
make seed      # Run seed data script
make clean     # Stop services and remove volumes
make test      # Run backend tests (if implemented)
```

## Success Criteria

- ✅ Admin can create sites
- ✅ Users with 'create' can create children
- ✅ Creator automatically gets 'manage'
- ✅ Permissions inherit to children
- ✅ Deny overrides inherited allow
- ✅ Group permissions work
- ✅ Permission UI shows effective permissions
- ✅ All test scenarios pass

## Project Structure

```
acl-poc/
├── docker-compose.yml          # Multi-container orchestration
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── Makefile                   # Common commands
│
├── backend/                   # FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── seed_data.py          # Database seeding
│   ├── alembic/
│   │   └── versions/         # Migration scripts
│   └── app/
│       ├── main.py           # FastAPI app entry
│       ├── config.py         # Settings
│       ├── database.py       # SQLAlchemy setup
│       ├── models/           # Database models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       ├── api/              # Route handlers
│       └── core/             # Utilities
│
├── frontend/                  # Vue 3 frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── api/              # API client
│       ├── stores/           # Pinia stores
│       ├── components/       # Vue components
│       ├── views/            # Page views
│       └── router/           # Vue Router
│
└── nginx/                     # Reverse proxy
    ├── Dockerfile
    └── nginx.conf
```

## Troubleshooting

### Services won't start

1. Check if ports 8080 is available:
   ```bash
   lsof -i :8080
   ```

2. View service logs:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   docker-compose logs nginx
   ```

### Database is locked

SQLite can have locking issues with concurrent access. If you see "database is locked" errors:

1. Stop all services: `docker-compose down`
2. Remove the database: `rm -rf data/`
3. Restart: `docker-compose up --build`

### Permission denied errors

The `data/` directory needs to be writable by the container:

```bash
mkdir -p data
chmod 777 data
```

## Security Notes

⚠️ **This is a PoC - not production ready!**

- Default credentials are weak (change in production)
- SQLite is not suitable for production (use PostgreSQL)
- JWT secret should be strong and kept secret
- HTTPS should be enabled for production
- Rate limiting should be added
- Input validation should be enhanced

## License

This is a proof-of-concept project for demonstration purposes.
