# ACL System PoC - Technical Specification v3

## Overview

Pure ACL system where **everything is a resource**, permissions are explicit, and **business logic is separated from ACL logic**. Groups are standalone grantees, not hierarchical resources.

```
┌─────────────────────────────────────────────────────────────┐
│                        STACK                                │
├─────────────────────────────────────────────────────────────┤
│  Frontend     │  Vue 3 + Vite + Pinia + TailwindCSS        │
│  Backend      │  FastAPI + Pydantic v2 + SQLAlchemy 2.0    │
│  Database     │  SQLite                                     │
│  Container    │  Docker Compose                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Principles

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE PRINCIPLES                          │
├─────────────────────────────────────────────────────────────┤
│  1. Everything is a resource (sites, plans, sensors, etc.) │
│  2. Group membership = 'member' permission on group         │
│  3. Permissions inherit downward in hierarchy               │
│  4. Groups are STANDALONE (grantees, not hierarchical)      │
│  5. Creators get 'manage' automatically                     │
│  6. Only is_admin bypasses all ACL checks                   │
│  7. Business logic separated from ACL logic                 │
│  8. Field-level access control supported                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   BUSINESS LAYER                          ACL LAYER                         │
│   (Data & Relationships)                  (Access Control)                  │
│                                                                             │
│   ┌─────────────────────┐                ┌─────────────────────┐           │
│   │ sites               │                │ resource_permissions│           │
│   │ plans (site_id FK)  │ ◄─────────────│                     │           │
│   │ sensors (plan_id FK)│    reads       │ Permission checks   │           │
│   │ brokers (plan_id FK)│    hierarchy   │ use FK config to    │           │
│   │ alarms (sensor_id)  │    from FKs    │ resolve ancestors   │           │
│   │ alerts (alarm_id)   │                │                     │           │
│   │ groups (standalone) │                │ Groups = grantees   │           │
│   └─────────────────────┘                └─────────────────────┘           │
│                                                                             │
│   Owns:                                   Owns:                             │
│   - Data integrity                        - Who can do what                 │
│   - Foreign keys                          - Field restrictions              │
│   - Business validation                   - Inheritance logic               │
│                                           - Expiration                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐         ┌─────────────────────────────┐  │
│   │   NGINX     │  :8080  │   Vue Frontend              │  │
│   │   (proxy)   │────────▶│   - Resource browser        │  │
│   │             │         │   - Permission manager      │  │
│   └──────┬──────┘         │   - Group membership UI     │  │
│          │                │   - Inheritance viewer      │  │
│          │ /api/*         └─────────────────────────────┘  │
│          ▼                                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │   FastAPI Backend                                   │  │
│   │   - Auth (JWT)                                      │  │
│   │   - ACL Service (permission checks)                 │  │
│   │   - Resource Services (business logic)              │  │
│   │   - Hierarchy Config                                │  │
│   └──────────────────────┬──────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │   SQLite  /data/acl.db                              │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Resource Hierarchy

### Hierarchy Configuration

```python
# ACL reads hierarchy from business tables via this config
HIERARCHY_CONFIG = {
    # Hierarchical resources (permissions inherit down)
    'alert': {'parent_type': 'alarm', 'parent_fk': 'alarm_id'},
    'alarm': {'parent_type': 'sensor', 'parent_fk': 'sensor_id'},
    'sensor': {'parent_type': 'plan', 'parent_fk': 'plan_id'},
    'broker': {'parent_type': 'plan', 'parent_fk': 'plan_id'},
    'plan': {'parent_type': 'site', 'parent_fk': 'site_id'},
    'site': {'parent_type': None, 'parent_fk': None},  # root
    
    # Standalone resources (no inheritance)
    'group': {'parent_type': None, 'parent_fk': None},
    'dashboard': {'parent_type': None, 'parent_fk': None},
}
```

### Visual Hierarchy

```
HIERARCHICAL (permissions inherit down):
═════════════════════════════════════════

    🏭 SITE (root)
     │
     └── 📋 PLAN
          │
          ├── 📡 SENSOR
          │    │
          │    └── 🔔 ALARM
          │         │
          │         └── ⚠️ ALERT
          │
          └── 📶 BROKER


STANDALONE (no inheritance):
═════════════════════════════════════════

    👥 GROUP      (grantee, can have perms on anything)
    📊 DASHBOARD  (owner-based)
```

---

## Data Model

### Complete Schema

```
┌──────────────────┐
│      users       │
├──────────────────┤
│ id          PK   │
│ username    UQ   │
│ password_hash    │
│ is_admin         │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      groups      │   ← Standalone, no hierarchy
├──────────────────┤
│ id          PK   │
│ name             │
│ description      │
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      sites       │
├──────────────────┤
│ id          PK   │
│ name             │
│ description      │
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      plans       │
├──────────────────┤
│ id          PK   │
│ name             │
│ description      │
│ site_id      FK  │──▶ sites.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│     sensors      │
├──────────────────┤
│ id          PK   │
│ name             │
│ field_a          │
│ field_b          │
│ field_c          │
│ field_d          │
│ field_e          │
│ plan_id      FK  │──▶ plans.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│     brokers      │
├──────────────────┤
│ id          PK   │
│ name             │
│ protocol         │
│ host             │
│ port             │
│ plan_id      FK  │──▶ plans.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│     alarms       │
├──────────────────┤
│ id          PK   │
│ name             │
│ threshold        │
│ condition        │
│ active           │
│ sensor_id    FK  │──▶ sensors.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│     alerts       │
├──────────────────┤
│ id          PK   │
│ message          │
│ severity         │
│ triggered_at     │
│ acknowledged     │
│ alarm_id     FK  │──▶ alarms.id
│ created_at       │
└──────────────────┘

┌──────────────────┐
│    dashboards    │
├──────────────────┤
│ id          PK   │
│ name             │
│ config      JSON │
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    resource_permissions                         │
│                  (THE source of truth for ACL)                  │
├─────────────────────────────────────────────────────────────────┤
│ id               PK   UUID                                      │
│ grantee_type          'user' | 'group'                         │
│ grantee_id            UUID                                      │
│ resource_type         'group'|'site'|'plan'|'sensor'|          │
│                       'broker'|'alarm'|'alert'|'dashboard'      │
│ resource_id           UUID                                      │
│ permission            'member'|'read'|'write'|'delete'|        │
│                       'create'|'manage'                         │
│ effect                'allow' | 'deny'                         │
│ inherit               BOOLEAN                                   │
│ fields                JSONB (nullable, ['a','b'] or null=all)  │
│ granted_by            UUID (nullable for system)               │
│ granted_at            TIMESTAMP                                 │
│ expires_at            TIMESTAMP (nullable)                     │
├─────────────────────────────────────────────────────────────────┤
│ UNIQUE (grantee_type, grantee_id, resource_type,               │
│         resource_id, permission)                                │
└─────────────────────────────────────────────────────────────────┘

INDEXES:
  idx_perm_grantee     (grantee_type, grantee_id)
  idx_perm_resource    (resource_type, resource_id)
  idx_perm_resolve     (resource_type, resource_id, permission)
  idx_perm_expires     (expires_at) WHERE expires_at IS NOT NULL

NO association tables. Everything is in resource_permissions.
```

---

## Permission Types

```
PERMISSION    VALID FOR              MEANING
──────────────────────────────────────────────────────────────
member        group only             User belongs to this group
read          all resources          Can view (respects fields)
write         all resources          Can modify (respects fields)
delete        all resources          Can remove resource
create        all resources          Can create children
manage        all resources          Full control + grant perms
```

### Permission Hierarchy

```
manage
  ├── create
  ├── delete
  └── write
        └── read
```

Checking `read` succeeds if user has any of: `read`, `write`, `delete`, `create`, `manage`.

### Field-Level Control

```
fields: NULL              → All fields accessible
fields: ['a', 'b', 'c']   → Only fields a, b, c accessible
fields: []                → No fields (permission exists but useless)

Resolution:
  Multiple permissions → Union of fields
  Any null → All fields (null wins)
```

---

## How Groups Work

### Groups are Standalone Grantees

```
┌─────────────────────────────────────────────────────────────────┐
│                     GROUPS IN ACL                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Groups are GRANTEES, not hierarchical resources.              │
│                                                                 │
│  A group can:                                                   │
│  • Have permissions on ANY resource (site, plan, sensor...)   │
│  • Have permissions on MULTIPLE sites                          │
│  • Be a grantee for 'member' permission                        │
│                                                                 │
│  A group does NOT:                                              │
│  • Inherit permissions from a parent                           │
│  • Have a site_id or parent reference                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Membership via ACL

```
"alice is member of ops-team"

INSERT INTO resource_permissions:
┌─────────────┬────────────┬───────────┬───────────┬────────┐
│ grantee_type│ grantee_id │ res_type  │ res_id    │ perm   │
├─────────────┼────────────┼───────────┼───────────┼────────┤
│ user        │ alice      │ group     │ ops-team  │ member │
└─────────────┴────────────┴───────────┴───────────┴────────┘
```

### Group Gets Permission on Resource

```
"ops-team can write factory-1 (with inheritance)"

INSERT INTO resource_permissions:
┌─────────────┬────────────┬───────────┬───────────┬────────┬────────┐
│ grantee_type│ grantee_id │ res_type  │ res_id    │ perm   │ inherit│
├─────────────┼────────────┼───────────┼───────────┼────────┼────────┤
│ group       │ ops-team   │ site      │ factory-1 │ write  │ true   │
└─────────────┴────────────┴───────────┴───────────┴────────┴────────┘
```

### "Site Admin" Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  "Site Admin" = User who has 'manage' on a site                │
│                 (directly or via group)                         │
│                                                                 │
│  It's NOT a flag. It's a permission query result.              │
│                                                                 │
│  SETUP:                                                         │
│    user:alice → group:factory1-admins → member                 │
│    group:factory1-admins → site:factory1 → manage (inherit)    │
│                                                                 │
│  RESULT:                                                        │
│    alice is "site admin" of factory1                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Permission Service

### Get Ancestors

```python
def get_ancestors(resource_type: str, resource_id: str) -> list:
    """
    Walk up hierarchy using HIERARCHY_CONFIG.
    Standalone resources return only themselves.
    """
    config = HIERARCHY_CONFIG.get(resource_type)
    
    # Standalone resource - no ancestors
    if not config or not config['parent_type']:
        return [(resource_type, resource_id, 0)]
    
    ancestors = [(resource_type, resource_id, 0)]
    current_type, current_id = resource_type, resource_id
    depth = 1
    
    while True:
        cfg = HIERARCHY_CONFIG.get(current_type)
        if not cfg or not cfg['parent_type']:
            break
        
        resource = db.get(current_type, current_id)
        parent_id = getattr(resource, cfg['parent_fk'])
        
        if not parent_id:
            break
        
        ancestors.append((cfg['parent_type'], parent_id, depth))
        current_type = cfg['parent_type']
        current_id = parent_id
        depth += 1
    
    return ancestors


# Examples:
get_ancestors('alert', 'alert-1')
# → [('alert','alert-1',0), ('alarm','alarm-1',1), 
#    ('sensor','sensor-1',2), ('plan','floor-a',3), ('site','factory1',4)]

get_ancestors('broker', 'mqtt-1')
# → [('broker','mqtt-1',0), ('plan','floor-a',1), ('site','factory1',2)]

get_ancestors('group', 'ops-team')
# → [('group','ops-team',0)]  # Standalone - no parents
```

### Check Algorithm

```python
def check(user_id, resource_type, resource_id, permission):
    """
    Returns: (allowed: bool, fields: list | None)
    """

    # 1. Admin bypass
    if user.is_admin:
        return (True, None)  # All fields

    # 2. Get user's groups
    groups = SELECT resource_id 
             FROM resource_permissions
             WHERE grantee_type = 'user'
               AND grantee_id = :user_id
               AND resource_type = 'group'
               AND permission = 'member'
               AND effect = 'allow'
               AND (expires_at IS NULL OR expires_at > NOW())

    # 3. Build grantee list
    grantees = [('user', user_id)] + [('group', g) for g in groups]

    # 4. Get ancestors (uses HIERARCHY_CONFIG)
    ancestors = get_ancestors(resource_type, resource_id)

    # 5. Expand permission
    perms = expand(permission)
    # e.g., 'read' → ['read','write','delete','create','manage']

    # 6. Single query
    results = SELECT effect, depth, inherit, fields
              FROM resource_permissions
              WHERE (grantee_type, grantee_id) IN :grantees
                AND (resource_type, resource_id) IN :ancestors
                AND permission IN :perms
                AND (expires_at IS NULL OR expires_at > NOW())
              ORDER BY depth ASC,     -- closest first
                       effect DESC    -- deny before allow

    # 7. Resolve with field aggregation
    allowed_fields = []
    
    for row in results:
        if row.depth > 0 and not row.inherit:
            continue
        
        if row.effect == 'deny':
            return (False, None)
        
        if row.effect == 'allow':
            if row.fields is None:
                return (True, None)  # All fields
            else:
                allowed_fields.extend(row.fields)
    
    if allowed_fields:
        return (True, list(set(allowed_fields)))
    
    # 8. Default deny
    return (False, None)
```

### Auto-Grant on Create

```python
def create_resource(user, resource_type, data):
    """
    Create resource with permission check and auto-grant.
    """
    
    # 1. Determine parent from HIERARCHY_CONFIG
    config = HIERARCHY_CONFIG.get(resource_type)
    
    if config and config['parent_fk']:
        parent_id = data.get(config['parent_fk'].replace('_id', '_id'))
        parent_type = config['parent_type']
        
        # Check create permission on parent
        allowed, _ = check(user.id, parent_type, parent_id, 'create')
        if not allowed:
            raise Forbidden("No create permission on parent")
    else:
        # Root/standalone resource - admin only
        if not user.is_admin:
            raise Forbidden("Only admin can create root resources")

    # 2. Insert resource
    resource = db.insert(resource_type, {
        **data,
        'created_by': user.id
    })

    # 3. Auto-grant manage to creator
    db.insert('resource_permissions', {
        'grantee_type': 'user',
        'grantee_id': user.id,
        'resource_type': resource_type,
        'resource_id': resource.id,
        'permission': 'manage',
        'effect': 'allow',
        'inherit': True,
        'fields': None,  # All fields
        'granted_by': None  # System
    })

    return resource
```

### Query Site Admins

```python
def get_site_admins(site_id: str) -> list[str]:
    """Get all user IDs who have 'manage' on this site."""
    
    # Get groups with manage on site
    admin_groups = SELECT grantee_id 
                   FROM resource_permissions
                   WHERE grantee_type = 'group'
                     AND resource_type = 'site'
                     AND resource_id = :site_id
                     AND permission = 'manage'
                     AND effect = 'allow'
    
    # Get users who are members of those groups
    users_via_groups = SELECT grantee_id
                       FROM resource_permissions
                       WHERE grantee_type = 'user'
                         AND resource_type = 'group'
                         AND resource_id IN :admin_groups
                         AND permission = 'member'
                         AND effect = 'allow'
    
    # Get users with direct manage permission
    users_direct = SELECT grantee_id
                   FROM resource_permissions
                   WHERE grantee_type = 'user'
                     AND resource_type = 'site'
                     AND resource_id = :site_id
                     AND permission = 'manage'
                     AND effect = 'allow'
    
    return list(set(users_via_groups + users_direct))
```

---

## API Endpoints

```
AUTH
────────────────────────────────────────────────────────────────
POST   /auth/login             {username, password} → {token}
GET    /auth/me                → current user + effective permissions

USERS (admin only)
────────────────────────────────────────────────────────────────
GET    /users                  → list users
POST   /users                  → create user
GET    /users/{id}             → get user + group memberships
DELETE /users/{id}             → delete user

GROUPS (standalone)
────────────────────────────────────────────────────────────────
GET    /groups                 → list groups (visible to user)
POST   /groups                 → create group (admin only)
GET    /groups/{id}            → get group
PUT    /groups/{id}            → update group
DELETE /groups/{id}            → delete group
GET    /groups/{id}/members    → list members (via permissions)
GET    /groups/{id}/permissions → list group's permissions on resources

SITES
────────────────────────────────────────────────────────────────
GET    /sites                  → list accessible sites
POST   /sites                  → create site (admin only)
GET    /sites/{id}             → get site
PUT    /sites/{id}             → update site
DELETE /sites/{id}             → delete site
GET    /sites/{id}/admins      → list site admins

PLANS
────────────────────────────────────────────────────────────────
GET    /plans                  → list accessible plans
GET    /sites/{site_id}/plans  → list plans for site
POST   /plans                  → create plan {site_id, name}
GET    /plans/{id}             → get plan
PUT    /plans/{id}             → update plan
DELETE /plans/{id}             → delete plan

SENSORS
────────────────────────────────────────────────────────────────
GET    /sensors                → list accessible sensors
GET    /plans/{plan_id}/sensors → list sensors for plan
POST   /sensors                → create sensor {plan_id, name, ...}
GET    /sensors/{id}           → get sensor
PUT    /sensors/{id}           → update sensor (field-level check)
DELETE /sensors/{id}           → delete sensor

BROKERS
────────────────────────────────────────────────────────────────
GET    /brokers                → list accessible brokers
GET    /plans/{plan_id}/brokers → list brokers for plan
POST   /brokers                → create broker {plan_id, name, ...}
GET    /brokers/{id}           → get broker
PUT    /brokers/{id}           → update broker
DELETE /brokers/{id}           → delete broker

ALARMS
────────────────────────────────────────────────────────────────
GET    /alarms                 → list accessible alarms
GET    /sensors/{sensor_id}/alarms → list alarms for sensor
POST   /alarms                 → create alarm {sensor_id, ...}
GET    /alarms/{id}            → get alarm
PUT    /alarms/{id}            → update alarm
DELETE /alarms/{id}            → delete alarm

ALERTS
────────────────────────────────────────────────────────────────
GET    /alerts                 → list accessible alerts
GET    /alarms/{alarm_id}/alerts → list alerts for alarm
GET    /alerts/{id}            → get alert
PUT    /alerts/{id}            → update alert (acknowledge)
DELETE /alerts/{id}            → delete alert

DASHBOARDS
────────────────────────────────────────────────────────────────
GET    /dashboards             → list accessible dashboards
POST   /dashboards             → create dashboard
GET    /dashboards/{id}        → get dashboard
PUT    /dashboards/{id}        → update dashboard
DELETE /dashboards/{id}        → delete dashboard

PERMISSIONS (unified ACL API)
────────────────────────────────────────────────────────────────
GET    /permissions            → my permissions
POST   /permissions            → grant permission
DELETE /permissions/{id}       → revoke permission
GET    /permissions/resource/{type}/{id}  → perms for resource
GET    /permissions/resource/{type}/{id}/effective → effective perms
POST   /permissions/check      → bulk permission check
GET    /permissions/inheritance/{type}/{id} → view inheritance chain
```

### Request Examples

```json
// Add alice to ops-team (group membership)
POST /permissions
{
  "grantee_type": "user",
  "grantee_id": "uuid-alice",
  "resource_type": "group",
  "resource_id": "uuid-ops-team",
  "permission": "member"
}

// Grant ops-team write on factory-1 with inheritance
POST /permissions
{
  "grantee_type": "group",
  "grantee_id": "uuid-ops-team",
  "resource_type": "site",
  "resource_id": "uuid-factory-1",
  "permission": "write",
  "inherit": true
}

// Grant with field restriction
POST /permissions
{
  "grantee_type": "group",
  "grantee_id": "uuid-operators",
  "resource_type": "site",
  "resource_id": "uuid-factory-1",
  "permission": "write",
  "inherit": true,
  "fields": ["field_a", "field_b", "field_c"]
}

// Deny bob access to floor-b specifically
POST /permissions
{
  "grantee_type": "user",
  "grantee_id": "uuid-bob",
  "resource_type": "plan",
  "resource_id": "uuid-floor-b",
  "permission": "read",
  "effect": "deny"
}

// Temporary membership (expires)
POST /permissions
{
  "grantee_type": "user",
  "grantee_id": "uuid-contractor",
  "resource_type": "group",
  "resource_id": "uuid-ops-team",
  "permission": "member",
  "expires_at": "2025-03-01T00:00:00Z"
}

// Make group a "site admin" group
POST /permissions
{
  "grantee_type": "group",
  "grantee_id": "uuid-factory1-admins",
  "resource_type": "site",
  "resource_id": "uuid-factory-1",
  "permission": "manage",
  "inherit": true
}
```

### Response Examples

```json
// GET /sensors/123 - with permissions
{
  "id": "123",
  "name": "Temperature Sensor",
  "field_a": "23.5",
  "field_b": "65",
  "field_c": "1013",
  "field_d": "2024-01-15",
  "field_e": "{\"interval\": 60}",
  "plan_id": "plan-1",
  "_permissions": {
    "can_read": true,
    "can_write": true,
    "writable_fields": ["field_a", "field_b", "field_c"],
    "can_delete": false,
    "can_manage": false
  }
}

// GET /permissions/inheritance/sensor/123
{
  "resource": {"type": "sensor", "id": "123", "name": "Temp Sensor"},
  "chain": [
    {"type": "sensor", "id": "123", "depth": 0},
    {"type": "plan", "id": "plan-1", "name": "Floor A", "depth": 1},
    {"type": "site", "id": "site-1", "name": "Factory 1", "depth": 2}
  ],
  "effective_permissions": {
    "read": {"allowed": true, "source": "group:ops-team via site:Factory 1"},
    "write": {"allowed": true, "fields": ["a","b","c"], "source": "group:ops-team via site:Factory 1"},
    "delete": {"allowed": false},
    "manage": {"allowed": false}
  }
}
```

---

## Directory Structure

```
acl-poc/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial.py
│   │
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── group.py
│       │   ├── site.py
│       │   ├── plan.py
│       │   ├── sensor.py
│       │   ├── broker.py
│       │   ├── alarm.py
│       │   ├── alert.py
│       │   ├── dashboard.py
│       │   └── permission.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── group.py
│       │   ├── site.py
│       │   ├── plan.py
│       │   ├── sensor.py
│       │   ├── broker.py
│       │   ├── alarm.py
│       │   ├── alert.py
│       │   ├── dashboard.py
│       │   └── permission.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── acl.py              # Core ACL service
│       │   ├── hierarchy.py        # Hierarchy config & traversal
│       │   └── resources.py        # Business logic
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── groups.py
│       │   ├── sites.py
│       │   ├── plans.py
│       │   ├── sensors.py
│       │   ├── brokers.py
│       │   ├── alarms.py
│       │   ├── alerts.py
│       │   ├── dashboards.py
│       │   └── permissions.py
│       │
│       └── core/
│           ├── __init__.py
│           ├── security.py
│           └── deps.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       │
│       ├── api/
│       │   ├── client.ts
│       │   ├── auth.ts
│       │   ├── resources.ts
│       │   └── permissions.ts
│       │
│       ├── stores/
│       │   ├── auth.ts
│       │   └── resources.ts
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.vue
│       │   │   ├── Header.vue
│       │   │   └── Breadcrumb.vue
│       │   ├── resources/
│       │   │   ├── ResourceTree.vue
│       │   │   ├── SiteCard.vue
│       │   │   ├── PlanCard.vue
│       │   │   ├── SensorCard.vue
│       │   │   ├── BrokerCard.vue
│       │   │   ├── AlarmCard.vue
│       │   │   └── AlertCard.vue
│       │   ├── permissions/
│       │   │   ├── PermissionBadge.vue
│       │   │   ├── PermissionModal.vue
│       │   │   ├── PermissionMatrix.vue
│       │   │   ├── InheritanceViewer.vue
│       │   │   ├── GrantForm.vue
│       │   │   └── FieldSelector.vue
│       │   ├── groups/
│       │   │   ├── GroupList.vue
│       │   │   ├── GroupMembers.vue
│       │   │   ├── GroupPermissions.vue
│       │   │   └── AddMemberModal.vue
│       │   └── users/
│       │       ├── UserProfile.vue
│       │       └── UserPermissions.vue
│       │
│       ├── views/
│       │   ├── Login.vue
│       │   ├── Dashboard.vue
│       │   ├── Sites.vue
│       │   ├── SiteDetail.vue
│       │   ├── PlanDetail.vue
│       │   ├── SensorDetail.vue
│       │   ├── Groups.vue
│       │   ├── GroupDetail.vue
│       │   ├── Users.vue
│       │   ├── UserDetail.vue
│       │   ├── Permissions.vue
│       │   └── MyPermissions.vue
│       │
│       └── router/
│           └── index.ts
│
└── nginx/
    ├── Dockerfile
    └── nginx.conf
```

---

## Frontend UI

### Main Navigation with Full Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESERVARIUM                                                    👤 alice ▼    │
├──────────────┬──────────────────────────────────────────────────────────────────┤
│              │                                                                  │
│  📊 Dashboard│                                                                  │
│              │                                                                  │
│  🏭 Sites    │                                                                  │
│  ├─ Factory 1│                                                                  │
│  │  ├─ 📋 Floor A                                                              │
│  │  │  ├─ 📡 Sensors                                                           │
│  │  │  │  ├─ Temp #1                                                           │
│  │  │  │  │  └─ 🔔 Alarms                                                      │
│  │  │  │  └─ Humidity #1                                                       │
│  │  │  └─ 📶 Brokers                                                           │
│  │  │     └─ MQTT #1                                                           │
│  │  └─ 📋 Floor B                                                              │
│  └─ Factory 2│                                                                  │
│              │                                                                  │
│  👥 Groups   │                                                                  │
│              │                                                                  │
│  👤 Users    │                                                                  │
│              │                                                                  │
│  🔐 Permissions                                                                 │
│              │                                                                  │
│  ⚙️ System   │                                                                  │
│              │                                                                  │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

### Groups List View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESERVARIUM                                                    👤 alice ▼    │
├──────────────┬──────────────────────────────────────────────────────────────────┤
│              │  👥 Groups                                      [+ Create Group] │
│  📊 Dashboard│                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│  🏭 Sites    │  │ 🔍 Search groups...                            Filter ▼    │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│ ▶👥 Groups   │                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│  👤 Users    │  │                                                             │ │
│              │  │  GROUP NAME              MEMBERS    PERMISSIONS      ACTIONS│ │
│  🔐 Permissions│  │  ─────────────────────────────────────────────────────────│ │
│              │  │                                                             │ │
│  ⚙️ System   │  │  👥 Factory 1 Admins        3       🔐 1 resource     ⋮    │ │
│              │  │     └─ manage: site:factory1 (inherit)                     │ │
│              │  │                                                             │ │
│              │  │  👥 Factory 1 Operators     8       🔐 1 resource     ⋮    │ │
│              │  │     └─ write: site:factory1 (fields: a,b,c)                │ │
│              │  │                                                             │ │
│              │  │  👥 Factory 1 Viewers      12       🔐 1 resource     ⋮    │ │
│              │  │     └─ read: site:factory1 (inherit)                       │ │
│              │  │                                                             │ │
│              │  │  👥 Global Operators        5       🔐 3 resources    ⋮    │ │
│              │  │     └─ write: site:factory1, site:factory2, site:factory3  │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
│              │  Showing 4 of 8 groups                          < 1 2 >         │
│              │                                                                  │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

### Group Detail View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESERVARIUM                                                    👤 alice ▼    │
├──────────────┬──────────────────────────────────────────────────────────────────┤
│              │  👥 Groups › Factory 1 Admins                     [Edit] [Delete]│
│  📊 Dashboard│                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│  🏭 Sites    │  │  OVERVIEW                                                   │ │
│              │  │                                                             │ │
│ ▶👥 Groups   │  │  Name:        Factory 1 Admins                             │ │
│              │  │  Description: Administrators for Factory 1 site            │ │
│  👤 Users    │  │  Created:     2024-01-15 by admin                          │ │
│              │  │  Members:     3 users                                       │ │
│  🔐 Permissions│  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│  ⚙️ System   │                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│              │  │  MEMBERS                                    [+ Add Member]  │ │
│              │  │                                                             │ │
│              │  │  👤 alice          alice@company.com           [Remove]    │ │
│              │  │  👤 bob            bob@company.com             [Remove]    │ │
│              │  │  👤 charlie        charlie@company.com         [Remove]    │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│              │  │  PERMISSIONS (what this group can access)  [+ Add Permission]│ │
│              │  │                                                             │ │
│              │  │  RESOURCE              PERMISSION   INHERIT  FIELDS  ACTIONS│ │
│              │  │  ───────────────────────────────────────────────────────────│ │
│              │  │  🏭 site:factory1      manage       ✓        All      ⋮    │ │
│              │  │     └─ Includes all plans, sensors, brokers, alarms        │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

### Site Detail View with Plans

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESERVARIUM                                                    👤 alice ▼    │
├──────────────┬──────────────────────────────────────────────────────────────────┤
│              │  🏭 Sites › Factory 1                             [Edit] [Delete]│
│  📊 Dashboard│                                                                  │
│              │  ┌────────────┬─────────────┬──────────────────────────────────┐ │
│  🏭 Sites    │  │  Overview  │  ▶ Plans    │         🔐 Permissions           │ │
│  ├▶Factory 1 │  └────────────┴─────────────┴──────────────────────────────────┘ │
│  │  ├─ 📋 Floor A                                                   [+ Add Plan]│
│  │  └─ 📋 Floor B│                                                              │
│  └─ Factory 2│  ┌─────────────────────────────────────────────────────────────┐ │
│              │  │                                                             │ │
│  👥 Groups   │  │  PLAN NAME           SENSORS    BROKERS    ALARMS   ACTIONS │ │
│              │  │  ─────────────────────────────────────────────────────────  │ │
│  👤 Users    │  │                                                             │ │
│              │  │  📋 Floor A             8          2         3    [View] ⋮  │ │
│  🔐 Permissions│  │     Production floor - main assembly                       │ │
│              │  │                                                             │ │
│  ⚙️ System   │  │  📋 Floor B            12          3         5    [View] ⋮  │ │
│              │  │     Warehouse and storage                                   │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
│              │  ┌─────────────────────────────────────────────────────────────┐ │
│              │  │  ADMINISTRATORS (users with 'manage')                       │ │
│              │  │                                                             │ │
│              │  │  👤 alice      via Factory 1 Admins                        │ │
│              │  │  👤 bob        via Factory 1 Admins                        │ │
│              │  │  👤 charlie    via Factory 1 Admins                        │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

### Sensor Detail with Field Permissions

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESERVARIUM                                                    👤 bob ▼      │
├──────────────┬──────────────────────────────────────────────────────────────────┤
│              │  🏭 Factory 1 › 📋 Floor A › 📡 Temp Sensor #1    [Edit] [Delete]│
│  📊 Dashboard│                                                                  │
│              │  ┌──────────┬────────────┬───────────┬────────────────────────┐  │
│  🏭 Sites    │  │▶Overview │  Readings  │  Alarms   │   🔐 Permissions       │  │
│  ├─ Factory 1│  └──────────┴────────────┴───────────┴────────────────────────┘  │
│  │  ├▶📋 Floor A                                                                │
│  │  │  ├▶📡 Sensors│  ┌─────────────────────────────────────────────────────┐ │
│  │  │  │  ├▶Temp #1│  │  ℹ️ You can edit fields: field_a, field_b, field_c  │ │
│  │  │  │  └─ ...   │  │     Other fields are read-only for your role        │ │
│  │  │  └─ 📶 Brokers│  └─────────────────────────────────────────────────────┘ │
│  │  └─ 📋 Floor B│                                                              │
│  └─ Factory 2│  ┌─────────────────────────────────────────────────────────────┐ │
│              │  │  SENSOR FIELDS                                              │ │
│  👥 Groups   │  │                                                             │ │
│              │  │  Field A (Temperature):           ✏️ Editable              │ │
│  👤 Users    │  │  ┌─────────────────────────────────────────────────────┐    │ │
│              │  │  │  23.5                                               │    │ │
│  🔐 Permissions│  │  └─────────────────────────────────────────────────────┘    │ │
│              │  │                                                             │ │
│  ⚙️ System   │  │  Field B (Humidity):              ✏️ Editable              │ │
│              │  │  ┌─────────────────────────────────────────────────────┐    │ │
│              │  │  │  65                                                 │    │ │
│              │  │  └─────────────────────────────────────────────────────┘    │ │
│              │  │                                                             │ │
│              │  │  Field C (Pressure):              ✏️ Editable              │ │
│              │  │  ┌─────────────────────────────────────────────────────┐    │ │
│              │  │  │  1013.25                                            │    │ │
│              │  │  └─────────────────────────────────────────────────────┘    │ │
│              │  │                                                             │ │
│              │  │  Field D (Calibration):           🔒 Read-only             │ │
│              │  │  ┌─────────────────────────────────────────────────────┐    │ │
│              │  │  │  ░░░░ 2024-01-15 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │ │
│              │  │  └─────────────────────────────────────────────────────┘    │ │
│              │  │                                                             │ │
│              │  │  Field E (Config):                🔒 Read-only             │ │
│              │  │  ┌─────────────────────────────────────────────────────┐    │ │
│              │  │  │  ░░░░ {"interval": 60} ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │ │
│              │  │  └─────────────────────────────────────────────────────┘    │ │
│              │  │                                                             │ │
│              │  └─────────────────────────────────────────────────────────────┘ │
│              │                                                                  │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  nginx:
    build: ./nginx
    ports:
      - "8080:80"
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=/api

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=sqlite:///./data/acl.db
      - SECRET_KEY=${SECRET_KEY:-dev-secret-change-me}
      - ADMIN_USER=${ADMIN_USER:-admin}
      - ADMIN_PASS=${ADMIN_PASS:-admin123}
    volumes:
      - ./data:/app/data
```

---

## Seed Data

```sql
-- Users
INSERT INTO users (id, username, password_hash, is_admin) VALUES
  ('u1', 'admin', '...', true),
  ('u2', 'alice', '...', false),
  ('u3', 'bob', '...', false),
  ('u4', 'carol', '...', false),
  ('u5', 'dave', '...', false),
  ('u6', 'eve', '...', false);

-- Groups (standalone - no site_id)
INSERT INTO groups (id, name, description) VALUES
  ('g1', 'Factory 1 Admins', 'Administrators for Factory 1'),
  ('g2', 'Factory 1 Operators', 'Operators for Factory 1'),
  ('g3', 'Factory 1 Viewers', 'Read-only access to Factory 1'),
  ('g4', 'Global Operators', 'Operators across all sites');

-- Sites
INSERT INTO sites (id, name, created_by) VALUES
  ('s1', 'Factory 1', 'u1'),
  ('s2', 'Factory 2', 'u1');

-- Plans
INSERT INTO plans (id, name, site_id, created_by) VALUES
  ('p1', 'Floor A', 's1', 'u1'),
  ('p2', 'Floor B', 's1', 'u1'),
  ('p3', 'Floor C', 's2', 'u1');

-- Sensors
INSERT INTO sensors (id, name, field_a, field_b, field_c, field_d, field_e, plan_id, created_by) VALUES
  ('se1', 'Temp Sensor #1', '23.5', '65', '1013', '2024-01-15', '{"interval":60}', 'p1', 'u1'),
  ('se2', 'Humidity Sensor #1', '65', '23', '1015', '2024-01-20', '{"interval":120}', 'p1', 'u1'),
  ('se3', 'Pressure Sensor #1', '1013', '24', '66', '2024-02-01', '{"interval":60}', 'p2', 'u1');

-- Brokers
INSERT INTO brokers (id, name, protocol, host, port, plan_id, created_by) VALUES
  ('b1', 'MQTT Broker #1', 'mqtt', '192.168.1.100', 1883, 'p1', 'u1'),
  ('b2', 'CoAP Gateway', 'coap', '192.168.1.101', 5683, 'p1', 'u1');

-- Alarms
INSERT INTO alarms (id, name, threshold, condition, active, sensor_id, created_by) VALUES
  ('a1', 'High Temperature', 30.0, 'gt', true, 'se1', 'u1'),
  ('a2', 'Low Humidity', 40.0, 'lt', true, 'se2', 'u1');

-- Alerts
INSERT INTO alerts (id, message, severity, triggered_at, acknowledged, alarm_id) VALUES
  ('al1', 'Temperature exceeded 30°C', 'warning', '2024-11-25 10:00:00', false, 'a1');

-- Dashboards
INSERT INTO dashboards (id, name, config, created_by) VALUES
  ('d1', 'Main Dashboard', '{"widgets":[]}', 'u2');

-- Permissions
INSERT INTO resource_permissions 
  (grantee_type, grantee_id, resource_type, resource_id, 
   permission, effect, inherit, fields) VALUES
  
  -- Group memberships
  ('user', 'u2', 'group', 'g1', 'member', 'allow', false, null),  -- alice in F1 Admins
  ('user', 'u3', 'group', 'g2', 'member', 'allow', false, null),  -- bob in F1 Operators
  ('user', 'u4', 'group', 'g3', 'member', 'allow', false, null),  -- carol in F1 Viewers
  ('user', 'u5', 'group', 'g2', 'member', 'allow', false, null),  -- dave in F1 Operators
  ('user', 'u5', 'group', 'g4', 'member', 'allow', false, null),  -- dave in Global Operators
  
  -- Group permissions on sites
  ('group', 'g1', 'site', 's1', 'manage', 'allow', true, null),   -- F1 Admins manage Factory 1
  ('group', 'g2', 'site', 's1', 'write', 'allow', true, '["field_a","field_b","field_c"]'),  -- F1 Operators write (limited fields)
  ('group', 'g3', 'site', 's1', 'read', 'allow', true, null),     -- F1 Viewers read Factory 1
  ('group', 'g4', 'site', 's1', 'write', 'allow', true, null),    -- Global Operators write Factory 1
  ('group', 'g4', 'site', 's2', 'write', 'allow', true, null),    -- Global Operators write Factory 2
  
  -- Direct permissions
  ('user', 'u5', 'plan', 'p1', 'write', 'allow', false, '["field_d","field_e"]'),  -- dave extra fields on Floor A
  ('user', 'u3', 'plan', 'p2', 'read', 'deny', true, null),       -- bob denied Floor B
  
  -- Dashboard (auto-granted to creator)
  ('user', 'u2', 'dashboard', 'd1', 'manage', 'allow', false, null);  -- alice owns dashboard
```

---

## Test Scenarios

```
SCENARIO 1: Group inheritance through full hierarchy
  alice in Factory 1 Admins
  Factory 1 Admins has manage on site:Factory 1 (inherit=true)
  → alice can manage Factory 1 ✓
  → alice can manage plan:Floor A ✓
  → alice can manage sensor:Temp #1 ✓
  → alice can manage alarm:High Temperature ✓
  → alice can manage alert:001 ✓
  → alice can manage broker:MQTT #1 ✓

SCENARIO 2: Field-level restrictions
  bob in Factory 1 Operators
  Factory 1 Operators has write on Factory 1 (fields: a,b,c)
  → bob can write field_a on Temp Sensor #1 ✓
  → bob can write field_b on Temp Sensor #1 ✓
  → bob can write field_c on Temp Sensor #1 ✓
  → bob CANNOT write field_d on Temp Sensor #1 ✗
  → bob CANNOT write field_e on Temp Sensor #1 ✗

SCENARIO 3: Field union from multiple permissions
  dave in Factory 1 Operators (write: a,b,c on Factory 1)
  dave has direct write (d,e) on Floor A
  → dave can write field_a,b,c on Floor A (from group) ✓
  → dave can write field_d,e on Floor A (direct) ✓
  → dave effective fields on Floor A = a,b,c,d,e ✓
  → dave can only write a,b,c on Floor B (no direct perm) ✓

SCENARIO 4: Explicit deny overrides inherited allow
  bob in Factory 1 Operators (has write on Factory 1)
  bob has DENY read on Floor B
  → bob cannot read Floor B ✗
  → bob cannot read sensors under Floor B ✗
  → bob cannot read alarms under Floor B sensors ✗
  → bob can still access Floor A ✓

SCENARIO 5: Standalone groups with multi-site access
  dave in Global Operators
  Global Operators has write on Factory 1 AND Factory 2
  → dave can write to Factory 1 and all children ✓
  → dave can write to Factory 2 and all children ✓
  → Group is NOT tied to any specific site ✓

SCENARIO 6: Creator auto-manage
  carol has create permission on Floor A
  carol creates new sensor
  → carol gets manage on new sensor automatically ✓
  → carol can grant permissions on new sensor ✓
  → carol can create alarms on new sensor ✓

SCENARIO 7: Dashboard owner-based permissions
  alice creates dashboard
  → alice gets manage on dashboard automatically ✓
  → alice can grant read to others ✓
  → bob cannot see dashboard (no permission) ✗

SCENARIO 8: Site admin query
  Query: Who are the admins of Factory 1?
  → alice (via Factory 1 Admins group with manage) ✓
  → Returns: [alice]

SCENARIO 9: Expiring membership
  contractor added to Factory 1 Operators (expires: yesterday)
  → contractor NOT in group anymore ✗
  → contractor cannot access Factory 1 ✗

SCENARIO 10: Hierarchy traversal for alarm
  Check: Can bob write to alarm:High Temperature?
  Ancestors: alarm → sensor:Temp #1 → plan:Floor A → site:Factory 1
  bob in F1 Operators → write on site:Factory 1 (inherit=true)
  → Permission found at depth 3, inherit=true
  → bob can write (fields: a,b,c) ✓
```

---

## Implementation Phases

```
PHASE 1: Backend Core (2 days)
────────────────────────────────────
├── SQLAlchemy models (all entities)
├── Pydantic schemas
├── Hierarchy config & traversal
├── ACL service (check, grant, revoke)
├── Auth (JWT)
└── Seed script

PHASE 2: Backend API (2 days)
────────────────────────────────────
├── All CRUD endpoints
├── Permission endpoints
├── Field-level validation
├── Auto-grant on create
├── Inheritance query endpoint
└── Tests

PHASE 3: Frontend Core (2 days)
────────────────────────────────────
├── Auth flow
├── Resource tree (full hierarchy)
├── Site/Plan/Sensor views
├── Broker/Alarm/Alert views
└── Navigation & breadcrumbs

PHASE 4: Frontend Permissions (2 days)
────────────────────────────────────
├── Permission modal
├── Groups view & members
├── Inheritance viewer
├── Field restrictions UI
├── User permissions view
└── My permissions

PHASE 5: Polish (1 day)
────────────────────────────────────
├── Error handling
├── Loading states
├── Docker final
└── README & docs
```

---

## Success Criteria

```
☐ Admin creates sites, plans, groups
☐ Membership via permission API works
☐ Groups are standalone (no site_id)
☐ Group permissions propagate to members
☐ Inheritance works through full hierarchy (site→plan→sensor→alarm→alert)
☐ Inheritance works for brokers (site→plan→broker)
☐ Field-level restrictions work
☐ Field union from multiple permissions works
☐ Deny overrides allow
☐ Expiring permissions work
☐ Creator gets auto-manage
☐ Dashboard owner-based permissions work
☐ "Site admin" query works (no magic flags)
☐ UI shows effective permissions
☐ UI shows inheritance chain
☐ UI shows field restrictions (editable vs read-only)
☐ All test scenarios pass
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                   PURE ACL v3 - FINAL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HIERARCHICAL RESOURCES (inherit permissions):                 │
│    site → plan → sensor → alarm → alert                        │
│                 → broker                                        │
│                                                                 │
│  STANDALONE RESOURCES (no inheritance):                        │
│    group      - grantee, can have perms on any resource        │
│    dashboard  - owner-based (creator auto-manage)              │
│                                                                 │
│  KEY FEATURES:                                                  │
│  ✓ Single table for all permissions (resource_permissions)    │
│  ✓ Groups as standalone grantees (NOT hierarchical)           │
│  ✓ Configurable hierarchy via HIERARCHY_CONFIG                │
│  ✓ Field-level access control                                  │
│  ✓ Permission inheritance with deny override                   │
│  ✓ Expiring permissions                                        │
│  ✓ Creator auto-manage                                         │
│  ✓ "Site admin" = user with 'manage' on site (no flags)       │
│  ✓ Full audit trail (granted_by, granted_at)                  │
│  ✓ Business logic separated from ACL logic                    │
│                                                                 │
│  TABLES:                                                        │
│    Business: users, groups, sites, plans, sensors, brokers,   │
│              alarms, alerts, dashboards                        │
│    ACL: resource_permissions                                    │
│                                                                 │
│  Association tables: 0                                          │
│  Magic flags: 0                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
