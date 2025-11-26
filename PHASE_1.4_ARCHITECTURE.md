# Phase 1.4: User as Resource Type - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ACL Permission System                       │
│                         (Phase 1.4)                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Resource Types                            │
├─────────────────────────────────────────────────────────────────┤
│  Hierarchical:        Standalone:                                │
│  • Site (root)        • Group        ← existing                  │
│    └─ Plan            • User         ← NEW in Phase 1.4          │
│       ├─ Sensor       • Dashboard    ← existing                  │
│       │  └─ Alarm                                                │
│       │     └─ Alert                                             │
│       └─ Broker                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Permission Flow for User Resources

```
┌─────────────────────────────────────────────────────────────────┐
│               User Permission Grant Flow                         │
└─────────────────────────────────────────────────────────────────┘

Admin/Authorized User
        │
        │ POST /api/users/{bob_id}/permissions
        │ { grantee: alice, permission: manage }
        ▼
┌──────────────────────┐
│  Users API Endpoint  │
│  (users.py)          │
└──────────┬───────────┘
           │
           │ 1. Verify target user exists
           │ 2. Check authorization (admin or manage permission)
           │ 3. Verify grantee exists
           ▼
┌──────────────────────┐
│ Permission Service   │
│ (permission_service) │
└──────────┬───────────┘
           │
           │ grant(resource_type='user', resource_id=bob_id, ...)
           ▼
┌──────────────────────┐
│ resource_permissions │ ← Database table
│ table                │
└──────────────────────┘
     grantee_type: user
     grantee_id: alice_id
     resource_type: user  ← NEW
     resource_id: bob_id
     permission: manage
     effect: allow
```

## Permission Check Flow for User Resources

```
┌─────────────────────────────────────────────────────────────────┐
│            User Permission Check Flow                            │
└─────────────────────────────────────────────────────────────────┘

Alice tries to update Bob
        │
        │ PUT /api/users/{bob_id}
        ▼
┌──────────────────────┐
│ Update User Endpoint │
│ (users.py)           │
└──────────┬───────────┘
           │
           │ Check if self-update → apply business rules
           │ If not self-update → check ACL
           ▼
┌──────────────────────┐
│ Permission Service   │
│ (permission_service) │
└──────────┬───────────┘
           │
           │ check(user=alice, resource_type='user',
           │       resource_id=bob_id, permission='write')
           │
           ├─► 1. Admin bypass? → Allow
           │
           ├─► 2. Get user's groups
           │
           ├─► 3. Get ancestors (user has none - standalone)
           │
           ├─► 4. Query permissions
           │      WHERE (grantee=alice OR grantee IN user's groups)
           │        AND resource_type='user' AND resource_id=bob_id
           │        AND permission IN [write, manage]
           │
           └─► 5. Resolve (DENY > ALLOW, field aggregation)
                    │
                    ▼
              ┌────────────┐
              │   Result   │
              │ (True/False│
              │  + fields) │
              └────────────┘
```

## Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│              resource_permissions Table Schema                   │
├─────────────────────────────────────────────────────────────────┤
│ id                UUID (Primary Key)                             │
│                                                                  │
│ grantee_type      ENUM('user', 'group')                         │
│ grantee_id        UUID                                          │
│                                                                  │
│ resource_type     ENUM('site', 'plan', 'sensor', 'broker',     │
│                       'alarm', 'alert', 'dashboard',            │
│                       'group', 'user')  ← 'user' is NEW         │
│ resource_id       UUID                                          │
│                                                                  │
│ permission        ENUM('read', 'write', 'delete',               │
│                       'create', 'manage', 'member')             │
│ effect            ENUM('allow', 'deny')                         │
│ inherit           BOOLEAN                                        │
│ fields            JSON (list of field names or null)            │
│ expires_at        TIMESTAMP (nullable)                          │
│                                                                  │
│ granted_by        UUID (FK → users.id)                          │
│ granted_at        TIMESTAMP                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Example Permission Records

```sql
-- Example 1: Alice can manage Bob
INSERT INTO resource_permissions (
    grantee_type, grantee_id,
    resource_type, resource_id,
    permission, effect, inherit
) VALUES (
    'user', 'alice-uuid',
    'user', 'bob-uuid',        ← User as resource
    'manage', 'allow', true
);

-- Example 2: HR group can read all users
INSERT INTO resource_permissions (
    grantee_type, grantee_id,
    resource_type, resource_id,
    permission, effect, inherit
) VALUES (
    'group', 'hr-group-uuid',
    'user', 'employee-1-uuid',  ← User as resource
    'read', 'allow', true
);
```

## API Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                  New User Permission APIs                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GET /api/users/{user_id}/permissions                           │
│  ├─ Lists permissions granted ON this user                      │
│  ├─ Auth: Admin or manage permission on user                    │
│  └─ Returns: List[PermissionResponse]                           │
│                                                                  │
│  POST /api/users/{user_id}/permissions                          │
│  ├─ Grants permission on this user                              │
│  ├─ Auth: Admin or manage permission on user                    │
│  ├─ Body: PermissionCreate (resource fields auto-set)           │
│  └─ Returns: PermissionResponse                                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                Existing APIs (Enhanced)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PUT /api/users/{user_id}                                       │
│  ├─ Now checks 'write' permission on user resource              │
│  ├─ Self-update business rules still apply                      │
│  └─ Field-level permissions enforced                            │
│                                                                  │
│  POST /api/permissions/check                                    │
│  ├─ Now works with resource_type='user'                         │
│  └─ Returns permission check results                            │
│                                                                  │
│  GET /api/permissions/resource/user/{user_id}                   │
│  ├─ Lists permissions on user (generic endpoint)                │
│  └─ Requires 'manage' permission                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Use Case Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│                       Scenario 1:                                │
│                   Team Lead Management                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Alice (Team Lead) → [manage] → Bob (Team Member)               │
│                                                                  │
│  Alice can:                                                      │
│  • Update Bob's profile (PUT /api/users/bob)                    │
│  • View Bob's permissions (GET /api/users/bob/permissions)      │
│  • Grant permissions on Bob to others                           │
│                                                                  │
│  Alice cannot:                                                   │
│  • Change Bob's is_admin status (business rule)                 │
│  • Change Bob's username (business rule)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Scenario 2:                                │
│                  Department-Wide Access                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HR Group → [read] → All Employees                              │
│                                                                  │
│  HR members can:                                                 │
│  • View employee profiles                                        │
│  • Read employee information                                     │
│                                                                  │
│  HR members cannot:                                              │
│  • Modify employee profiles (no write permission)               │
│  • Delete employees                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Scenario 3:                                │
│                  Field-Level Restrictions                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Bob (User) → [write: email, password] → Bob (Self)             │
│                                                                  │
│  Bob can:                                                        │
│  • Update his email                                              │
│  • Change his password                                           │
│                                                                  │
│  Bob cannot:                                                     │
│  • Change his is_admin status                                    │
│  • Modify his username                                           │
│  • Change his disabled flag                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component Integration                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Frontend UI    │
│   (Vue.js)       │
└────────┬─────────┘
         │
         │ HTTP Requests
         ▼
┌──────────────────┐
│   API Router     │
│   (FastAPI)      │
├──────────────────┤
│ • auth.py        │
│ • users.py       │ ← Enhanced with permission endpoints
│ • permissions.py │ ← Enhanced with user resource support
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Permission       │
│ Service          │ ← Handles all permission logic
├──────────────────┤
│ • check()        │
│ • grant()        │
│ • revoke()       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Hierarchy        │
│ Service          │ ← Treats users as standalone
├──────────────────┤
│ • get_ancestors()│
│ • HIERARCHY_CFG  │ ← 'user': {parent: None}
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Database       │
│   (PostgreSQL)   │
├──────────────────┤
│ • users          │
│ • groups         │
│ • resource_perms │ ← Stores user permissions
└──────────────────┘
```

## Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│                   Authorization Hierarchy                        │
└─────────────────────────────────────────────────────────────────┘

Level 1: Admin Override
├─ is_admin = True → Bypass all checks
└─ Can do anything with any user

Level 2: Self-Update Rules (Business Logic)
├─ Non-admin users updating themselves
├─ Cannot change: is_admin, disabled, username
└─ Applied BEFORE ACL checks

Level 3: ACL Permissions (Resource-Based)
├─ Permission checks on user resources
├─ Evaluated when user != target_user
├─ Permission hierarchy: manage > write/read/delete/create
└─ Field-level restrictions apply

Level 4: Default Deny
└─ No permission = Access denied
```

## Permission Hierarchy

```
manage
  ├─── read
  ├─── write
  ├─── delete
  └─── create

Standalone permissions:
  • member (group membership only)
```

## Standalone vs Hierarchical Resources

```
Hierarchical Resources (inherit permissions):
┌─────────┐
│  Site   │ ← Permission granted here
└────┬────┘
     │ inherits down
┌────▼────┐
│  Plan   │
└────┬────┘
     │ inherits down
┌────▼────┐
│ Sensor  │ ← Also has permission

Standalone Resources (no inheritance):
┌─────────┐
│  User   │ ← Permission ONLY on this user
└─────────┘

┌─────────┐
│  Group  │ ← Permission ONLY on this group
└─────────┘

┌─────────┐
│Dashboard│ ← Permission ONLY on this dashboard
└─────────┘
```

## Implementation Summary

**What Changed:**
1. ✅ USER added to ResourceType enum (models + schemas)
2. ✅ User added to HIERARCHY_CONFIG as standalone
3. ✅ User added to model mapping
4. ✅ Resource name handler supports users
5. ✅ Resource validation for user/group resources
6. ✅ New API endpoints for user permissions
7. ✅ Frontend types updated

**What Didn't Change:**
- Database schema (no migration needed)
- Existing API endpoints (enhanced, not broken)
- Permission service core logic
- Hierarchy traversal logic
- Frontend UI (types only)

**Backwards Compatibility:**
- ✅ All existing permissions continue to work
- ✅ No breaking changes to APIs
- ✅ Additive changes only
