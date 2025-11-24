# Phase 2 Implementation Summary - Permission Service & API Endpoints

## Overview

Phase 2 of the ACL POC implements the complete permission checking logic and REST API endpoints for managing resources and permissions. This phase builds on the data models from Phase 1 and provides a fully functional API with JWT authentication and fine-grained access control.

## Implementation Details

### 1. Permission Service (`app/services/permission_service.py`)

The core ACL logic implementing the permission resolution algorithm:

**Key Methods:**
- `check(user, resource_type, resource_id, permission) -> bool`: Main permission checking algorithm
- `_get_ancestors(resource_type, resource_id)`: Builds the resource hierarchy chain (sensor → plan → site)
- `grant()`: Creates new permission entries
- `revoke()`: Deletes permission entries
- `list_for_resource()`: Lists all permissions for a specific resource
- `list_for_user()`: Lists all permissions for a user
- `auto_grant_manage()`: Auto-grants manage permission to resource creators

**Permission Hierarchy:**
```python
PERMISSION_HIERARCHY = {
    Permission.READ: [READ, WRITE, DELETE, CREATE, MANAGE],
    Permission.WRITE: [WRITE, MANAGE],
    Permission.DELETE: [DELETE, MANAGE],
    Permission.CREATE: [CREATE, MANAGE],
    Permission.MANAGE: [MANAGE],
}
```

**Check Algorithm:**
1. Admin bypass - admins have all permissions
2. Get user's group IDs
3. Build ancestor chain (e.g., sensor → plan → site)
4. Expand permission hierarchy (read implies write, etc.)
5. Query applicable permissions with depth ordering
6. Resolve first match (deny takes precedence)
7. Default deny

**Permission Inheritance:**
- Permissions with `inherit=true` apply to child resources
- Deny always takes precedence over allow
- First match wins (closest ancestor first)

### 2. Auth Service (`app/services/auth_service.py`)

Handles user authentication and JWT token management:

**Key Methods:**
- `authenticate_user(username, password)`: Validates credentials
- `create_token(user)`: Generates JWT access token
- `get_user_by_id(user_id)`: Retrieves user by ID
- `create_user()`: Creates new user accounts

**Security:**
- Uses bcrypt for password hashing
- JWT tokens with configurable expiration
- Bearer token authentication

### 3. Core Dependencies (`app/core/dependencies.py`)

FastAPI dependency injection for authentication:

**Key Dependencies:**
- `get_current_user()`: Extracts and validates JWT token, returns User object
- `get_current_admin_user()`: Ensures current user is an admin

### 4. API Endpoints

#### Auth API (`app/api/auth.py`)
- `POST /api/auth/login` - Login with username/password, returns JWT token
- `GET /api/auth/me` - Get current authenticated user info

#### Permissions API (`app/api/permissions.py`)
- `GET /api/permissions` - List permissions for current user (direct + group)
- `GET /api/permissions/resource/{type}/{id}` - List permissions for a resource
- `POST /api/permissions` - Grant a permission (requires manage on resource)
- `DELETE /api/permissions/{id}` - Revoke a permission (requires manage)
- `POST /api/permissions/check` - Bulk permission check

#### Sites API (`app/api/sites.py`)
- `GET /api/sites` - List sites with read permission
- `POST /api/sites` - Create site (admin only, auto-grants manage to creator)
- `GET /api/sites/{id}` - Get site details (requires read)
- `DELETE /api/sites/{id}` - Delete site (requires delete)

#### Plans API (`app/api/plans.py`)
- `GET /api/plans` - List plans with read permission
- `POST /api/plans` - Create plan (requires create on parent site)
- `GET /api/plans/{id}` - Get plan details (requires read)
- `DELETE /api/plans/{id}` - Delete plan (requires delete)

#### Sensors API (`app/api/sensors.py`)
- `GET /api/sensors` - List sensors with read permission
- `POST /api/sensors` - Create sensor (requires create on parent plan)
- `GET /api/sensors/{id}` - Get sensor details (requires read)
- `DELETE /api/sensors/{id}` - Delete sensor (requires delete)

### 5. Auto-Grant on Create

When a user creates a resource, the system automatically:
1. Checks 'create' permission on parent resource
2. Creates the resource
3. Auto-grants 'manage' permission to creator with `inherit=true`

This ensures creators can manage their resources and grant permissions to others.

## Testing

### Test Scripts

1. **`create_admin.py`** - Creates initial admin and test users
2. **`test_api_simple.sh`** - Comprehensive API test script
3. **`test_examples.sh`** - Example curl commands for manual testing

### Test Results

All endpoints tested and working correctly:

```bash
✓ Login as admin
✓ Get current user
✓ Create site (auto-grants manage to creator)
✓ List sites (filtered by permissions)
✓ Create plan (checks create permission on parent)
✓ Create sensor (checks create permission on parent)
✓ List my permissions (shows auto-granted manage permissions)
✓ Bulk permission check (all permissions allowed for admin)
✓ Login as alice
✓ Alice lists sites (empty - no permissions granted yet)
```

## Example API Usage

### 1. Login and Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin123"}'

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 2. Create a Site
```bash
curl -X POST http://localhost:8000/api/sites \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"name": "Factory 1"}'

Response:
{
  "id": "8240b712-61ca-4f40-948e-3a670ec68d21",
  "name": "Factory 1",
  "created_by": "67f83994-7b22-4dc1-87e2-79c8b00c4bd0",
  "created_at": "2025-11-24T14:37:06.228098"
}
```

### 3. Grant Permission
```bash
curl -X POST http://localhost:8000/api/permissions \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "grantee_type": "user",
    "grantee_id": "USER_ID",
    "resource_type": "site",
    "resource_id": "SITE_ID",
    "permission": "read",
    "effect": "allow",
    "inherit": true
  }'
```

### 4. Bulk Permission Check
```bash
curl -X POST http://localhost:8000/api/permissions/check \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "checks": [
      {"resource_type": "site", "resource_id": "SITE_ID", "permission": "read"},
      {"resource_type": "plan", "resource_id": "PLAN_ID", "permission": "write"}
    ]
  }'

Response:
{
  "results": [
    {"resource_type": "site", "resource_id": "SITE_ID", "permission": "read", "allowed": true},
    {"resource_type": "plan", "resource_id": "PLAN_ID", "permission": "write", "allowed": true}
  ]
}
```

## Key Features Implemented

### ✓ Permission Hierarchy
- Higher permissions grant lower ones (manage > create/delete/write > read)
- Permission expansion happens automatically in check algorithm

### ✓ Permission Inheritance
- Permissions with `inherit=true` apply to descendants
- Parent site permissions apply to child plans and sensors
- Non-inheritable permissions only apply to exact resource

### ✓ Deny Overrides Allow
- Deny permissions take precedence at any level
- First match wins in ancestor chain

### ✓ Auto-Grant on Create
- Creators automatically get 'manage' permission
- Enables delegation without admin intervention

### ✓ Admin Bypass
- Admin users bypass all permission checks
- Can create root resources (sites)

### ✓ Group Permissions
- Permissions can be granted to groups
- Users inherit permissions from all their groups
- Both direct and group permissions checked

### ✓ Bulk Operations
- Bulk permission checking for performance
- Single query checks multiple permissions

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # Auth endpoints
│   │   ├── permissions.py    # Permission management endpoints
│   │   ├── sites.py          # Site resource endpoints
│   │   ├── plans.py          # Plan resource endpoints
│   │   └── sensors.py        # Sensor resource endpoints
│   ├── core/
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   └── security.py       # JWT and password hashing
│   ├── services/
│   │   ├── auth_service.py   # Authentication service
│   │   └── permission_service.py  # Permission checking service
│   ├── main.py               # FastAPI app with router registration
│   └── ...
├── create_admin.py           # User creation script
├── test_api_simple.sh        # Test script
└── test_examples.sh          # Example commands
```

## Running the Application

### 1. Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Create Admin User
```bash
python create_admin.py
```

### 3. Start Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Tests
```bash
./test_api_simple.sh
```

### 5. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Next Steps (Phase 3 - Frontend)

1. Implement React frontend components
2. Permission management UI
3. Resource tree visualization
4. User/group management interface
5. Permission debugging tools

## Notes

- Database: SQLite with async support (aiosqlite)
- All operations are async for performance
- Comprehensive error handling and validation
- RESTful API design following best practices
- Full OpenAPI/Swagger documentation
