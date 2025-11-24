# ACL PoC Backend - Phase 2 Complete

This is a fully functional FastAPI backend implementing a pure ACL system with hybrid inheritance for hierarchical resources. Phase 2 includes all API endpoints, permission checking, and comprehensive testing.

## What's Included

### 1. Database Models (`app/models/`)

All models use SQLAlchemy 2.0 async style:

- **User** (`user.py`): User accounts with authentication
  - Fields: id, username, password_hash, is_admin, created_at
  - Relationships: groups (many-to-many), permissions

- **Group** (`group.py`): User groups for permission aggregation
  - Fields: id, name, created_at
  - Relationships: users (many-to-many), permissions
  - Association table: `group_users`

- **ResourcePermission** (`permission.py`): Core ACL table
  - Fields: id, grantee_type, grantee_id, resource_type, resource_id, permission, effect, inherit, granted_by, granted_at
  - Enums: GranteeType (user/group), ResourceType (site/plan/sensor), Permission (read/write/delete/create/manage), Effect (allow/deny)

- **Site** (`site.py`): Top-level resource
  - Fields: id, name, created_by, created_at
  - Relationships: plans (one-to-many)

- **Plan** (`plan.py`): Mid-level resource
  - Fields: id, name, site_id, created_by, created_at
  - Relationships: site (many-to-one), sensors (one-to-many)

- **Sensor** (`sensor.py`): Leaf-level resource
  - Fields: id, name, plan_id, created_by, created_at
  - Relationships: plan (many-to-one)

### 2. Pydantic Schemas (`app/schemas/`)

All schemas use Pydantic v2:

- **user.py**: UserCreate, UserResponse, UserLogin, Token
- **group.py**: GroupCreate, GroupResponse, GroupMemberAdd
- **permission.py**: PermissionCreate, PermissionResponse, PermissionCheck, PermissionCheckRequest, PermissionCheckResponse
- **resource.py**: SiteCreate/Response, PlanCreate/Response, SensorCreate/Response

### 3. Core Services (`app/services/`)

- **AuthService** (`auth_service.py`):
  - `authenticate_user()`: Verify username/password
  - `create_user()`: Create new user with hashed password
  - `create_token()`: Generate JWT token
  - `get_user_by_id()`: Fetch user
  - `get_all_users()`: List all users

- **PermissionService** (`permission_service.py`):
  - `check()`: Main permission check with inheritance
  - `_get_ancestors()`: Build resource hierarchy chain
  - `grant()`: Grant a permission
  - `revoke()`: Revoke a permission
  - `list_for_resource()`: List permissions on a resource
  - `list_for_user()`: List user's permissions
  - `auto_grant_manage()`: Auto-grant manage to creator

### 4. Security Utilities (`app/core/`)

- **security.py**:
  - `verify_password()`: Bcrypt password verification
  - `get_password_hash()`: Bcrypt password hashing
  - `create_access_token()`: JWT token generation
  - `decode_access_token()`: JWT token decoding

- **dependencies.py**:
  - `get_current_user()`: FastAPI dependency for authenticated user
  - `get_current_admin_user()`: FastAPI dependency for admin users

### 5. Configuration

- **config.py**: Pydantic Settings with environment variables
  - DATABASE_URL
  - SECRET_KEY
  - ALGORITHM
  - ACCESS_TOKEN_EXPIRE_MINUTES
  - ADMIN_USERNAME
  - ADMIN_PASSWORD

- **database.py**: SQLAlchemy async setup
  - AsyncEngine
  - AsyncSessionLocal
  - Base declarative class
  - `get_db()` dependency

### 6. Database Migrations

- **alembic.ini**: Alembic configuration
- **alembic/env.py**: Migration environment with all models imported
- **alembic/script.py.mako**: Migration template
- **alembic/versions/**: Migration scripts (generated via `alembic revision --autogenerate`)

### 7. Docker Configuration

- **Dockerfile**: Python 3.11 with all dependencies
- **requirements.txt**: All Python packages (FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, bcrypt, JWT)

## Permission System Design

### Hierarchy

```
Site (root)
 └── Plan
      └── Sensor
```

### Permission Types

- **read**: View resource
- **write**: Modify resource
- **delete**: Remove resource
- **create**: Create children
- **manage**: All above + grant permissions

### Permission Hierarchy (Implied Permissions)

- **manage** implies: write, delete, create, read
- **write** implies: read
- **delete** implies: read
- **create** implies: read

### Resolution Algorithm

1. **Admin bypass**: If user is admin, allow
2. **Get user groups**: Collect all group IDs
3. **Build ancestor chain**: Get parent resources up to root
4. **Expand permission**: Include implied permissions
5. **Query permissions**: Check user + group permissions on resource and ancestors
6. **Resolve**: First DENY wins, then first ALLOW wins
7. **Default deny**: If no match, deny

### Inheritance

Permissions with `inherit=true` apply to child resources.

Example:
- User has `read` on Site with `inherit=true`
- User can read all Plans and Sensors under that Site
- Unless explicitly denied

## Quick Start

### 1. Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create admin user
python create_admin.py
```

### 2. Run Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test
```bash
# Run comprehensive test
./test_api_simple.sh

# Test permission inheritance
./test_inheritance.sh
```

### 4. Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Default Users

Created by `create_admin.py`:

| Username | Password  | Role    |
|----------|-----------|---------|
| admin    | admin123  | Admin   |
| alice    | alice123  | User    |
| bob      | bob123    | User    |

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Resources
- `GET /api/sites` - List accessible sites
- `POST /api/sites` - Create site (admin only)
- `GET /api/sites/{id}` - Get site details
- `DELETE /api/sites/{id}` - Delete site

- `GET /api/plans` - List accessible plans
- `POST /api/plans` - Create plan (requires create on site)
- `GET /api/plans/{id}` - Get plan details
- `DELETE /api/plans/{id}` - Delete plan

- `GET /api/sensors` - List accessible sensors
- `POST /api/sensors` - Create sensor (requires create on plan)
- `GET /api/sensors/{id}` - Get sensor details
- `DELETE /api/sensors/{id}` - Delete sensor

### Permissions
- `GET /api/permissions` - List my permissions
- `GET /api/permissions/resource/{type}/{id}` - List resource permissions
- `POST /api/permissions` - Grant permission
- `DELETE /api/permissions/{id}` - Revoke permission
- `POST /api/permissions/check` - Bulk permission check

## Test Results

### Basic API Test (`test_api_simple.sh`)
```
✓ Login as admin
✓ Get current user
✓ Create site (auto-grants manage)
✓ List sites (filtered by permissions)
✓ Create plan (checks create permission)
✓ Create sensor (checks create permission)
✓ List permissions (shows auto-granted permissions)
✓ Bulk permission check (all allowed for admin)
✓ Login as alice
✓ Alice lists sites (empty - no permissions)
```

### Inheritance Test (`test_inheritance.sh`)
```
✓ Grant READ on site with inheritance
✓ Alice can access sensor via inheritance
✓ Bulk check shows inherited permissions
✓ Grant DENY on plan
✓ DENY blocks access to sensor
✓ DENY overrides inherited ALLOW
```

## Next Steps (Phase 3 - Frontend)

1. React components for resource management
2. Permission management UI
3. Resource tree visualization
4. User/group management interface
5. Permission debugging tools

## Database Schema

The database uses SQLite for simplicity. Schema includes:

- `users`: User accounts
- `groups`: User groups
- `group_users`: Many-to-many association
- `resource_permissions`: Core ACL table
- `sites`: Top-level resources
- `plans`: Mid-level resources
- `sensors`: Leaf resources

All tables have proper foreign keys and indexes for performance.
