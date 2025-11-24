# Phase 1 Backend Implementation - Complete

## Overview

Phase 1 of the ACL PoC backend is now complete. This phase establishes the core infrastructure, data models, and permission system logic.

## File Structure Created

```
/workspace/main/acl-poc/
├── .env.example                    # Environment variables template
├── backend/
│   ├── Dockerfile                  # Python 3.11 container
│   ├── requirements.txt            # All dependencies
│   ├── alembic.ini                 # Database migration config
│   ├── README.md                   # Phase 1 documentation
│   │
│   ├── alembic/
│   │   ├── env.py                  # Migration environment
│   │   ├── script.py.mako          # Migration template
│   │   └── versions/               # Migration scripts (to be generated)
│   │
│   └── app/
│       ├── main.py                 # FastAPI application
│       ├── config.py               # Settings (Pydantic)
│       ├── database.py             # SQLAlchemy async setup
│       │
│       ├── models/                 # SQLAlchemy 2.0 models
│       │   ├── __init__.py
│       │   ├── user.py             # User model
│       │   ├── group.py            # Group + group_users table
│       │   ├── permission.py       # ResourcePermission (core ACL)
│       │   ├── site.py             # Site resource
│       │   ├── plan.py             # Plan resource
│       │   └── sensor.py           # Sensor resource
│       │
│       ├── schemas/                # Pydantic v2 schemas
│       │   ├── __init__.py
│       │   ├── user.py             # User schemas + Token
│       │   ├── group.py            # Group schemas
│       │   ├── permission.py       # Permission schemas + checks
│       │   └── resource.py         # Site/Plan/Sensor schemas
│       │
│       ├── services/               # Business logic
│       │   ├── __init__.py
│       │   ├── auth_service.py     # Authentication & user management
│       │   └── permission_service.py # ACL check algorithm
│       │
│       ├── api/                    # API routes (Phase 2)
│       │   └── __init__.py
│       │
│       └── core/                   # Utilities
│           ├── __init__.py
│           ├── security.py         # JWT + bcrypt
│           └── dependencies.py     # FastAPI dependencies
```

## Implementation Details

### 1. Database Models (6 files)

All models use **SQLAlchemy 2.0 async style**:

✓ **User Model** (`models/user.py`)
  - UUID primary key
  - Username (unique, indexed)
  - Password hash (bcrypt)
  - is_admin flag
  - Timestamps
  - Relationships: groups, permissions

✓ **Group Model** (`models/group.py`)
  - UUID primary key
  - Name (unique, indexed)
  - Timestamps
  - Many-to-many with users via `group_users` table
  - Relationships: users, permissions

✓ **ResourcePermission Model** (`models/permission.py`) - **CORE ACL TABLE**
  - UUID primary key
  - Grantee: type (user/group) + ID
  - Resource: type (site/plan/sensor) + ID
  - Permission: read/write/delete/create/manage
  - Effect: allow/deny
  - Inherit: boolean (for child resources)
  - Metadata: granted_by, granted_at
  - Enums: GranteeType, ResourceType, Permission, Effect

✓ **Site Model** (`models/site.py`)
  - UUID primary key
  - Name (indexed)
  - created_by (FK to users)
  - Timestamps
  - Relationships: plans

✓ **Plan Model** (`models/plan.py`)
  - UUID primary key
  - Name (indexed)
  - site_id (FK to sites)
  - created_by (FK to users)
  - Timestamps
  - Relationships: site, sensors

✓ **Sensor Model** (`models/sensor.py`)
  - UUID primary key
  - Name (indexed)
  - plan_id (FK to plans)
  - created_by (FK to users)
  - Timestamps
  - Relationships: plan

### 2. Pydantic Schemas (4 files)

All schemas use **Pydantic v2** with `from_attributes = True`:

✓ **User Schemas** (`schemas/user.py`)
  - UserCreate, UserResponse, UserLogin, Token

✓ **Group Schemas** (`schemas/group.py`)
  - GroupCreate, GroupResponse, GroupMemberAdd

✓ **Permission Schemas** (`schemas/permission.py`)
  - PermissionCreate, PermissionResponse
  - PermissionCheck, PermissionCheckRequest, PermissionCheckResponse
  - Enums matching model enums

✓ **Resource Schemas** (`schemas/resource.py`)
  - SiteCreate/Response
  - PlanCreate/Response
  - SensorCreate/Response

### 3. Core Services (2 files)

✓ **AuthService** (`services/auth_service.py`)
  - authenticate_user(): Verify credentials
  - create_user(): Hash password, create user
  - create_token(): Generate JWT
  - get_user_by_id(): Fetch user
  - get_all_users(): List users

✓ **PermissionService** (`services/permission_service.py`) - **KEY IMPLEMENTATION**
  - check(): Main permission check with inheritance
    1. Admin bypass
    2. Get user groups
    3. Build ancestor chain
    4. Expand permission (manage → write, delete, etc.)
    5. Query permissions (user + groups, resource + ancestors)
    6. Resolve (DENY wins, then ALLOW)
    7. Default deny
  - _get_ancestors(): Build resource hierarchy (sensor → plan → site)
  - grant(): Create permission
  - revoke(): Delete permission
  - list_for_resource(): List resource permissions
  - list_for_user(): List user permissions
  - auto_grant_manage(): Auto-grant on creation

### 4. Security & Core (3 files)

✓ **Security** (`core/security.py`)
  - verify_password(): Bcrypt verification
  - get_password_hash(): Bcrypt hashing
  - create_access_token(): JWT generation with expiry
  - decode_access_token(): JWT decoding

✓ **Dependencies** (`core/dependencies.py`)
  - get_current_user(): Extract user from JWT token
  - get_current_admin_user(): Require admin role

✓ **Config** (`config.py`)
  - Pydantic Settings
  - Environment variables: DATABASE_URL, SECRET_KEY, ADMIN credentials

✓ **Database** (`database.py`)
  - AsyncEngine (SQLAlchemy 2.0)
  - AsyncSessionLocal factory
  - Base declarative class
  - get_db() dependency

### 5. FastAPI Application

✓ **Main App** (`main.py`)
  - FastAPI instance
  - CORS middleware
  - Root & health endpoints
  - Placeholder for Phase 2 routes

### 6. Database Migrations

✓ **Alembic Setup**
  - alembic.ini: Configuration
  - alembic/env.py: Environment with all models imported
  - alembic/script.py.mako: Migration template
  - Ready for: `alembic revision --autogenerate -m "Initial"`

### 7. Docker & Dependencies

✓ **Dockerfile**
  - Python 3.11-slim base
  - Installs all dependencies
  - Creates /app/data directory
  - Runs migrations + uvicorn

✓ **requirements.txt**
  - fastapi==0.109.0
  - uvicorn[standard]==0.27.0
  - sqlalchemy==2.0.25
  - alembic==1.13.1
  - pydantic==2.5.3
  - pydantic-settings==2.1.0
  - python-jose[cryptography]==3.3.0
  - passlib[bcrypt]==1.7.4
  - python-multipart==0.0.6
  - aiosqlite==0.19.0

## Permission System Architecture

### Resource Hierarchy
```
Site (root)
 └── Plan
      └── Sensor
```

### Permission Resolution Flow

```
┌─────────────────────────────────────────────────────────┐
│  check(user, resource_type, resource_id, permission)   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  user.is_admin = True? │
         └────────┬────────────────┘
                  │
        ┌─────────┴─────────┐
       YES                 NO
        │                   │
        ▼                   ▼
    ✓ ALLOW    ┌─────────────────────────┐
               │ Get user's group IDs    │
               └────────┬────────────────┘
                        │
                        ▼
               ┌─────────────────────────┐
               │ Build ancestor chain:   │
               │ sensor → plan → site    │
               └────────┬────────────────┘
                        │
                        ▼
               ┌─────────────────────────┐
               │ Expand permission:      │
               │ read → [read, write,    │
               │  delete, create, manage]│
               └────────┬────────────────┘
                        │
                        ▼
               ┌─────────────────────────┐
               │ For each ancestor:      │
               │   Query permissions for │
               │   user + groups         │
               └────────┬────────────────┘
                        │
                        ▼
               ┌─────────────────────────┐
               │ DENY found?             │
               └────────┬────────────────┘
                        │
                   ┌────┴────┐
                  YES       NO
                   │         │
                   ▼         ▼
               ✗ DENY   ┌─────────────┐
                        │ ALLOW found?│
                        └──────┬──────┘
                               │
                          ┌────┴────┐
                         YES       NO
                          │         │
                          ▼         ▼
                      ✓ ALLOW   ✗ DENY
                                (default)
```

### Permission Hierarchy (Implied)

```
manage ──┬──> write
         ├──> delete
         ├──> create
         └──> read

write ───────> (none)

delete ──────> (none)

create ──────> (none)

read ────────> (none)
```

When checking for `read`, the service also checks if user has `write`, `delete`, `create`, or `manage`.

### Inheritance Example

```
User has permission:
  grantee: user:alice
  resource: site:Factory1
  permission: read
  inherit: true

Alice can:
  ✓ Read site:Factory1
  ✓ Read plan:FloorA (child of Factory1)
  ✓ Read sensor:Temp1 (child of FloorA)
```

## Key Design Decisions

1. **Pure ACL**: Single source of truth in `resource_permissions` table
2. **Hybrid Inheritance**: Permissions inherit unless overridden by deny
3. **Permission Hierarchy**: Higher permissions imply lower ones
4. **Admin Bypass**: System admins skip all checks
5. **Group Aggregation**: User permissions = user perms + all group perms
6. **Default Deny**: No permission = denied
7. **DENY Wins**: Explicit deny overrides inherited allow
8. **Async All The Way**: SQLAlchemy 2.0 async, FastAPI async

## Testing the Setup

To verify Phase 1 is working:

```bash
cd /workspace/main/acl-poc/backend

# Install dependencies
pip install -r requirements.txt

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

## What's NOT Included (Phase 2)

- ❌ API endpoints (auth, users, groups, permissions, resources)
- ❌ Seed data script
- ❌ Database initialization with admin user
- ❌ Integration tests
- ❌ Auto-grant on resource creation logic in endpoints
- ❌ Bulk permission check endpoint
- ❌ Frontend integration

## Summary

✅ **33 files created**
✅ **6 database models** (User, Group, ResourcePermission, Site, Plan, Sensor)
✅ **4 schema modules** (User, Group, Permission, Resource)
✅ **2 service classes** (AuthService, PermissionService)
✅ **Core security** (JWT, bcrypt, dependencies)
✅ **Permission algorithm** (check with inheritance)
✅ **Alembic setup** (ready for migrations)
✅ **Docker ready** (Dockerfile + requirements.txt)
✅ **FastAPI app** (main.py with CORS)

**Phase 1 Status: COMPLETE**

Ready for Phase 2 implementation.
