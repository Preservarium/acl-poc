# Pure ACL Architecture - Final Design Document v3

## Executive Summary

Unified permission system where everything is a resource, every permission is explicit, hierarchy is configurable, and field-level access control is supported.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORE PRINCIPLES                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Everything is a resource (groups, sites, sensors, etc.)    │
│  2. Group membership = 'member' permission on group             │
│  3. Permissions inherit downward unless overridden              │
│  4. Parent-child via config (ACL reads from business FKs)       │
│  5. Groups are standalone (no ACL hierarchy)                    │
│  6. Field-level control via optional fields constraint          │
│  7. Creators get 'manage' automatically                         │
│  8. Only is_admin bypasses all checks                           │
│  9. "Site Admin" = has 'manage' on site (no magic flags)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   BUSINESS LAYER                        ACL LAYER                           │
│   (Data & Relationships)                (Access Control)                    │
│                                                                             │
│   ┌─────────────────────┐              ┌─────────────────────┐             │
│   │ sites               │              │ resource_permissions│             │
│   │ plans (site_id FK)  │◄────────────│                     │             │
│   │ sensors (plan_id FK)│   reads      │ Permission checks   │             │
│   │ brokers (plan_id FK)│   hierarchy  │ use FK config to    │             │
│   │ alarms (sensor_id)  │   from FKs   │ resolve ancestors   │             │
│   │ alerts (alarm_id)   │              │                     │             │
│   │ groups (standalone) │              │ Groups are grantees │             │
│   │ dashboards          │              │ not hierarchical    │             │
│   └─────────────────────┘              └─────────────────────┘             │
│                                                                             │
│   Owns:                                 Owns:                               │
│   - Data integrity                      - Who can do what                   │
│   - Foreign keys                        - Field restrictions                │
│   - Business rules                      - Inheritance logic                 │
│   - Self-update constraints             - Expiration                        │
│   - Validation                          - Deny overrides                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Distinction:**
- If `groups.site_id` exists in business layer → Used for UI organization only ("Groups in Factory 1")
- ACL does NOT use `groups.site_id` for permission inheritance
- Groups can have permissions on ANY resource, across multiple sites

---

## Data Model

### Business Tables (Own Relationships)

```
┌──────────────────┐
│      users       │
├──────────────────┤
│ id          PK   │
│ username    UQ   │
│ email            │
│ password_hash    │
│ is_admin    BOOL │  ← System admin (bypasses ALL checks)
│ disabled    BOOL │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      groups      │
├──────────────────┤
│ id          PK   │
│ name             │
│ description      │
│ site_id*     FK  │───▶ sites.id (OPTIONAL, for UI organization only)
│ created_by   FK  │
│ created_at       │
└──────────────────┘
* site_id is NOT used by ACL for hierarchy

┌──────────────────┐
│      sites       │
├──────────────────┤
│ id          PK   │
│ name             │
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      plans       │
├──────────────────┤
│ id          PK   │
│ name             │
│ site_id      FK  │───▶ sites.id
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
│ plan_id      FK  │───▶ plans.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│     brokers      │
├──────────────────┤
│ id          PK   │
│ name             │
│ config       JSON│
│ plan_id      FK  │───▶ plans.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      alarms      │
├──────────────────┤
│ id          PK   │
│ name             │
│ threshold        │
│ sensor_id    FK  │───▶ sensors.id
│ created_by   FK  │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│      alerts      │
├──────────────────┤
│ id          PK   │
│ triggered_at     │
│ value            │
│ alarm_id     FK  │───▶ alarms.id
│ created_at       │
└──────────────────┘

┌──────────────────┐
│    dashboards    │
├──────────────────┤
│ id          PK   │
│ name             │
│ config       JSON│
│ created_by   FK  │  ← Owner (auto-granted 'manage')
│ created_at       │
└──────────────────┘

┌──────────────────┐
│  System Config   │
│  (admin write,   │
│   all read)      │
├──────────────────┤
│ hardware         │
│ datatype         │
│ protocol         │
│ parser           │
│ manufacturer     │
│ communication_   │
│   mode           │
└──────────────────┘
```

### ACL Table (Owns Permissions)

```
┌─────────────────────────────────────────────────────────────────┐
│                    resource_permissions                         │
├─────────────────────────────────────────────────────────────────┤
│ id               PK   UUID                                      │
│ grantee_type          'user' | 'group'                          │
│ grantee_id            UUID                                      │
│ resource_type         'group'|'site'|'plan'|'sensor'|'broker'| │
│                       'alarm'|'alert'|'dashboard'|'user'|      │
│                       'hardware'|'datatype'|'protocol'|...     │
│ resource_id           UUID                                      │
│ permission            'member'|'read'|'write'|'delete'|        │
│                       'create'|'manage'                         │
│ effect                'allow' | 'deny'                          │
│ inherit               BOOLEAN                                   │
│ fields                JSONB (nullable, ['a','b'] or null=all)   │
│ granted_by            UUID (nullable for system)                │
│ granted_at            TIMESTAMP                                 │
│ expires_at            TIMESTAMP (nullable)                      │
├─────────────────────────────────────────────────────────────────┤
│ UNIQUE (grantee_type, grantee_id, resource_type,                │
│         resource_id, permission)                                │
└─────────────────────────────────────────────────────────────────┘

INDEXES:
  idx_perm_grantee     (grantee_type, grantee_id)
  idx_perm_resource    (resource_type, resource_id)
  idx_perm_resolve     (resource_type, resource_id, permission)
  idx_perm_expires     (expires_at) WHERE expires_at IS NOT NULL
```

---

## Hierarchy Configuration

### Resource Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESOURCE CATEGORIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HIERARCHICAL (permissions inherit down):                       │
│    site → plan → sensor → alarm → alert                        │
│                 → broker                                        │
│                                                                 │
│  STANDALONE (no inheritance, direct permissions only):          │
│    group      - grantee, can have perms on anything            │
│    dashboard  - owner-based (creator auto-manage)              │
│    user       - special self-update business rules             │
│                                                                 │
│  SYSTEM CONFIG (admin write, authenticated read):              │
│    hardware, datatype, protocol, parser,                       │
│    manufacturer, communication_mode                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Parent-Child Mapping (Application Config)

```python
# ACL reads hierarchy from business tables via this config
HIERARCHY_CONFIG = {
    # === HIERARCHICAL RESOURCES ===
    # Permissions inherit from parent to children
    
    'sensor': {
        'parent_type': 'plan',
        'parent_fk': 'plan_id',
    },
    'broker': {
        'parent_type': 'plan',
        'parent_fk': 'plan_id',
    },
    'alarm': {
        'parent_type': 'sensor',
        'parent_fk': 'sensor_id',
    },
    'alert': {
        'parent_type': 'alarm',
        'parent_fk': 'alarm_id',
    },
    'plan': {
        'parent_type': 'site',
        'parent_fk': 'site_id',
    },
    'site': {
        'parent_type': None,  # root resource
        'parent_fk': None,
    },
    
    # === STANDALONE RESOURCES ===
    # No inheritance - permissions must be granted directly
    
    'group': {
        'parent_type': None,
        'parent_fk': None,
    },
    'dashboard': {
        'parent_type': None,
        'parent_fk': None,
    },
    'user': {
        'parent_type': None,
        'parent_fk': None,
    },
    
    # === SYSTEM CONFIG RESOURCES ===
    # Admin write, authenticated read (see RESOURCE_DEFAULTS)
    
    'hardware': {
        'parent_type': None,
        'parent_fk': None,
    },
    'datatype': {
        'parent_type': None,
        'parent_fk': None,
    },
    'protocol': {
        'parent_type': None,
        'parent_fk': None,
    },
    'parser': {
        'parent_type': None,
        'parent_fk': None,
    },
    'manufacturer': {
        'parent_type': None,
        'parent_fk': None,
    },
    'communication_mode': {
        'parent_type': None,
        'parent_fk': None,
    },
}

# Default permissions for resource types (checked before default deny)
RESOURCE_DEFAULTS = {
    'hardware': {'authenticated_read': True, 'admin_only_write': True},
    'datatype': {'authenticated_read': True, 'admin_only_write': True},
    'protocol': {'authenticated_read': True, 'admin_only_write': True},
    'parser': {'authenticated_read': True, 'admin_only_write': True},
    'manufacturer': {'authenticated_read': True, 'admin_only_write': True},
    'communication_mode': {'authenticated_read': True, 'admin_only_write': True},
}
```

### Visual Hierarchy

```
PERMISSION INHERITANCE (ACL):
═══════════════════════════════

    site (root)
         │
         ├── plan
         │    ├── sensor
         │    │    └── alarm
         │    │         └── alert
         │    └── broker
         │
         └── (more plans...)


NO INHERITANCE (Standalone):
════════════════════════════

    group       (can have permissions on ANY resource)
    
    dashboard   (owner-based via creator auto-manage)
    
    user        (special business rules for self-update)
    
    hardware    (system config - authenticated read)
    datatype    
    protocol    
    parser      
    manufacturer
    communication_mode
```

### Get Parent Function

```python
def get_parent(resource_type: str, resource_id: str) -> tuple | None:
    """
    ACL layer reads parent from business tables.
    Returns None for standalone resources.
    """
    config = HIERARCHY_CONFIG.get(resource_type)
    if not config or not config['parent_type']:
        return None  # Standalone resource
    
    resource = db.get(resource_type, resource_id)
    parent_id = getattr(resource, config['parent_fk'])
    
    if parent_id is None:
        return None
    
    return (config['parent_type'], parent_id)
```

### Get Ancestors Function

```python
def get_ancestors(resource_type: str, resource_id: str) -> list:
    """
    Walk up the hierarchy using config.
    Returns [(type, id, depth), ...] from self to root.
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
        parent = get_parent(current_type, current_id)
        if not parent:
            break
        
        parent_type, parent_id = parent
        ancestors.append((parent_type, parent_id, depth))
        current_type, current_id = parent_type, parent_id
        depth += 1
    
    return ancestors


# Examples:

get_ancestors('sensor', 'temp-1')
# → [('sensor','temp-1',0), ('plan','floor-a',1), ('site','factory1',2)]

get_ancestors('alarm', 'high-temp')
# → [('alarm','high-temp',0), ('sensor','temp-1',1), 
#    ('plan','floor-a',2), ('site','factory1',3)]

get_ancestors('group', 'operators')
# → [('group','operators',0)]  # Standalone - no parents

get_ancestors('dashboard', 'my-dash')
# → [('dashboard','my-dash',0)]  # Standalone - no parents

get_ancestors('hardware', 'device-x')
# → [('hardware','device-x',0)]  # Standalone - no parents
```

---

## Permission System

### Permission Types

```
PERMISSION    APPLIES TO         MEANING
─────────────────────────────────────────────────────────────────
member        group              User belongs to this group
read          resources          Can view (respects fields filter)
write         resources          Can modify (respects fields filter)
delete        resources          Can remove
create        resources          Can create children
manage        all                Full control + can grant perms
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
fields: []                → No fields accessible (unusual)
```

**Field Resolution:**
```
User has multiple permissions on same resource:
  - write with fields=['a','b']
  - write with fields=['c']
  
Result: Union of fields = ['a','b','c']

User has permission with null fields:
  - write with fields=null
  
Result: null wins (all fields accessible)
```

---

## Permission Resolution Algorithm

### Check Permission

```python
def check(user, resource_type, resource_id, permission):
    """
    Returns: (allowed: bool, fields: list | None)
    """
    
    # 1. System admin bypass
    if user.is_admin:
        return (True, None)  # All fields
    
    # 2. Get user's groups (membership = 'member' permission on group)
    groups = db.query("""
        SELECT resource_id FROM resource_permissions
        WHERE grantee_type = 'user'
          AND grantee_id = :user_id
          AND resource_type = 'group'
          AND permission = 'member'
          AND effect = 'allow'
          AND (expires_at IS NULL OR expires_at > NOW())
    """, user_id=user.id)
    
    # 3. Build grantees list
    grantees = [('user', user.id)] + [('group', g) for g in groups]
    
    # 4. Get ancestors (standalone resources return only self)
    ancestors = get_ancestors(resource_type, resource_id)
    
    # 5. Expand permission to include implied
    perms = expand_permission(permission)
    
    # 6. Query all applicable permissions
    results = db.query("""
        SELECT effect, depth, inherit, fields
        FROM resource_permissions
        WHERE (grantee_type, grantee_id) IN :grantees
          AND (resource_type, resource_id) IN :ancestors
          AND permission IN :perms
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY depth ASC,    -- closest first
                 effect DESC   -- deny before allow
    """, grantees=grantees, ancestors=ancestors, perms=perms)
    
    # 7. Resolve with field aggregation
    allowed_fields = []
    
    for row in results:
        # Skip non-inheritable permissions from ancestors
        if row.depth > 0 and not row.inherit:
            continue
        
        # Deny wins immediately
        if row.effect == 'deny':
            return (False, None)
        
        # Allow with fields
        if row.effect == 'allow':
            if row.fields is None:
                return (True, None)  # All fields
            else:
                allowed_fields.extend(row.fields)
    
    # 8. Check if any fields were allowed
    if allowed_fields:
        return (True, list(set(allowed_fields)))
    
    # 9. Check resource defaults (system config entities)
    defaults = RESOURCE_DEFAULTS.get(resource_type, {})
    if permission == 'read' and defaults.get('authenticated_read'):
        return (True, None)  # All fields readable
    
    # 10. Default deny
    return (False, None)
```

### Expand Permission

```python
PERMISSION_IMPLIES = {
    'read':   ['read', 'write', 'delete', 'create', 'manage'],
    'write':  ['write', 'manage'],
    'delete': ['delete', 'manage'],
    'create': ['create', 'manage'],
    'manage': ['manage'],
    'member': ['member'],
}

def expand_permission(permission):
    return PERMISSION_IMPLIES.get(permission, [permission])
```

### Check Field Access

```python
def check_field_access(user, resource_type, resource_id, permission, field):
    """Check if user can access a specific field."""
    allowed, fields = check(user, resource_type, resource_id, permission)
    
    if not allowed:
        return False
    
    if fields is None:
        return True  # All fields allowed
    
    return field in fields
```

---

## Groups in Pure ACL

```
┌─────────────────────────────────────────────────────────────────┐
│                     GROUPS ARE STANDALONE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Groups are GRANTEES, not hierarchical resources.              │
│                                                                 │
│  A group can:                                                   │
│  • Have permissions on ANY resource (site, plan, sensor...)    │
│  • Have permissions on MULTIPLE sites                          │
│  • Be a grantee for 'member' permission (group membership)     │
│                                                                 │
│  A group does NOT:                                              │
│  • Inherit permissions from a parent                            │
│  • Pass permissions to child groups                             │
│  • Use site_id for ACL purposes (business layer only)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Cross-Site Group

```
┌─────────────────────────────────────────────────────────────────┐
│ group: "Global Operators"                                       │
│                                                                 │
│ Permissions (in resource_permissions):                          │
│   → write on site:factory1 (inherit=true)                       │
│   → write on site:factory2 (inherit=true)                       │
│   → read on site:factory3 (inherit=true)                        │
│                                                                 │
│ This group spans multiple sites - NOT tied to one               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Site Admin Pattern

**"Site Admin" = User who has 'manage' permission on a site (directly or via group)**

There is NO magic flag. It's a permission query result.

### How It Works

```
SETUP (all in resource_permissions table):

  ┌────────────────┐
  │  user:alice    │
  └───────┬────────┘
          │
          │ permission: 'member'
          │ resource_type: 'group'
          │ resource_id: 'factory1-admins'
          ▼
  ┌────────────────────┐
  │ group:factory1-    │
  │       admins       │
  └───────┬────────────┘
          │
          │ permission: 'manage'
          │ resource_type: 'site'
          │ resource_id: 'factory1'
          │ inherit: true
          ▼
  ┌────────────────┐
  │ site:factory1  │
  └────────────────┘

RESULT:
  alice → member of factory1-admins → factory1-admins has manage on factory1
  ∴ alice is "site admin" of factory1
```

### Multiple Admin Groups

```
┌─────────────────────────────────────────────────────────────────┐
│                     site:factory1                               │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │ manage             │ manage             │ manage
         │                    │                    │
┌────────┴───────┐  ┌────────┴───────┐  ┌────────┴───────┐
│ group:factory1 │  │ group:global   │  │ user:eve       │
│ -admins        │  │ -superops      │  │ (direct grant) │
└────────────────┘  └────────────────┘  └────────────────┘
         ▲                    ▲
         │ member             │ member
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │  alice  │          │  bob    │
    └─────────┘          └─────────┘

ALL THREE are "site admins" of factory1:
  - alice (via factory1-admins group)
  - bob (via global-superops group)  
  - eve (direct permission)
```

### Query: Is User a Site Admin?

```python
async def get_user_admin_sites(self, user_id: str) -> list[str]:
    """Get all site IDs where user has 'manage' permission."""
    
    if await self.is_system_admin(user_id):
        return await self.site_repository.get_all_site_ids()
    
    # Check via groups and direct grants
    return await db.query("""
        -- Sites via group membership
        SELECT DISTINCT rp_site.resource_id AS site_id
        FROM resource_permissions rp_member
        JOIN resource_permissions rp_site 
            ON rp_site.grantee_type = 'group'
            AND rp_site.grantee_id = rp_member.resource_id
        WHERE 
            rp_member.grantee_type = 'user'
            AND rp_member.grantee_id = :user_id
            AND rp_member.resource_type = 'group'
            AND rp_member.permission = 'member'
            AND rp_member.effect = 'allow'
            AND (rp_member.expires_at IS NULL OR rp_member.expires_at > NOW())
            AND rp_site.resource_type = 'site'
            AND rp_site.permission = 'manage'
            AND rp_site.effect = 'allow'
            AND (rp_site.expires_at IS NULL OR rp_site.expires_at > NOW())
        
        UNION
        
        -- Sites via direct grant
        SELECT resource_id AS site_id
        FROM resource_permissions
        WHERE grantee_type = 'user'
            AND grantee_id = :user_id
            AND resource_type = 'site'
            AND permission = 'manage'
            AND effect = 'allow'
            AND (expires_at IS NULL OR expires_at > NOW())
    """, user_id=user_id)


async def is_site_admin(self, user_id: str, site_id: str) -> bool:
    """Check if user is admin of a specific site."""
    # This is just a permission check!
    allowed, _ = await self.check(
        user_id=user_id,
        resource_type='site',
        resource_id=site_id,
        permission='manage'
    )
    return allowed
```

---

## Resource Creation

### Auto-Grant Pattern

```python
def create_resource(user, resource_type, data, parent_type=None, parent_id=None):
    """
    Create resource with permission check and auto-grant.
    """
    
    # 1. Check create permission on parent (for hierarchical resources)
    if parent_type and parent_id:
        allowed, _ = check(user, parent_type, parent_id, 'create')
        if not allowed:
            raise Forbidden("No create permission on parent")
    else:
        # Root/standalone resource
        config = HIERARCHY_CONFIG.get(resource_type, {})
        defaults = RESOURCE_DEFAULTS.get(resource_type, {})
        
        # System config resources require admin
        if defaults.get('admin_only_write'):
            if not user.is_admin:
                raise Forbidden("Only admin can create system config")
        # Root hierarchical resources (sites) require admin
        elif config.get('parent_type') is None and resource_type == 'site':
            if not user.is_admin:
                raise Forbidden("Only admin can create sites")
        # Standalone resources (dashboard, group) - user creates own
    
    # 2. Insert resource (business layer handles FK)
    resource = db.insert(resource_type, {
        **data,
        'created_by': user.id
    })
    
    # 3. Auto-grant manage to creator (except system config)
    if not RESOURCE_DEFAULTS.get(resource_type, {}).get('admin_only_write'):
        db.insert('resource_permissions', {
            'grantee_type': 'user',
            'grantee_id': user.id,
            'resource_type': resource_type,
            'resource_id': resource.id,
            'permission': 'manage',
            'effect': 'allow',
            'inherit': True,
            'fields': None,
            'granted_by': None  # System
        })
    
    return resource
```

---

## Permission Patterns

### Pattern 1: Site Admin via Group

```
SETUP:
  resource_permissions:
  ┌─────────────┬────────────────┬────────┬────────┬────────┐
  │ Grantee     │ Resource       │ Perm   │ Inherit│ Fields │
  ├─────────────┼────────────────┼────────┼────────┼────────┤
  │ user:alice  │ group:f1-admin │ member │ -      │ -      │
  │ group:f1-adm│ site:factory1  │ manage │ true   │ null   │
  └─────────────┴────────────────┴────────┴────────┴────────┘

EFFECTIVE:
  alice → member of f1-admins
  f1-admins → manage on factory1 (inherit=true)
  
  alice can:
  ✓ manage factory1
  ✓ manage all plans under factory1 (inherited)
  ✓ manage all sensors, brokers under plans (inherited)
  ✓ manage all alarms under sensors (inherited)
  ✓ manage all alerts under alarms (inherited)
  ✓ create new plans, sensors, brokers, alarms
```

### Pattern 2: Limited Write with Field Restriction

```
SETUP:
  resource_permissions:
  ┌─────────────┬────────────────┬────────┬────────┬─────────────┐
  │ Grantee     │ Resource       │ Perm   │ Inherit│ Fields      │
  ├─────────────┼────────────────┼────────┼────────┼─────────────┤
  │ user:bob    │ group:f1-ops   │ member │ -      │ -           │
  │ group:f1-ops│ site:factory1  │ write  │ true   │ [a,b,c]     │
  └─────────────┴────────────────┴────────┴────────┴─────────────┘

EFFECTIVE:
  bob can:
  ✓ read factory1 and all children (write implies read)
  ✓ write fields a,b,c on all sensors
  ✗ write fields d,e on sensors
  ✗ delete any resource
  ✗ create new resources
```

### Pattern 3: Cross-Site Group

```
SETUP:
  groups table:
    id: 'global-viewers', name: 'Global Viewers'
    (no site_id or site_id ignored by ACL)

  resource_permissions:
  ┌─────────────────┬────────────────┬────────┬────────┬────────┐
  │ Grantee         │ Resource       │ Perm   │ Inherit│ Fields │
  ├─────────────────┼────────────────┼────────┼────────┼────────┤
  │ user:eve        │ grp:global-view│ member │ -      │ -      │
  │ grp:global-view │ site:factory1  │ read   │ true   │ null   │
  │ grp:global-view │ site:factory2  │ read   │ true   │ null   │
  │ grp:global-view │ site:factory3  │ read   │ true   │ null   │
  └─────────────────┴────────────────┴────────┴────────┴────────┘

EFFECTIVE:
  eve can:
  ✓ read factory1, factory2, factory3 and all their children
  ✗ write anything
  
  Group spans multiple sites via explicit grants
```

### Pattern 4: Deny Override

```
SETUP:
  resource_permissions:
  ┌─────────────┬────────────────┬────────┬────────┬────────┐
  │ Grantee     │ Resource       │ Perm   │ Inherit│ Effect │
  ├─────────────┼────────────────┼────────┼────────┼────────┤
  │ user:dave   │ group:ops      │ member │ -      │ allow  │
  │ group:ops   │ site:factory1  │ write  │ true   │ allow  │
  │ user:dave   │ plan:floor-b   │ read   │ true   │ DENY   │
  └─────────────┴────────────────┴────────┴────────┴────────┘

EFFECTIVE:
  dave can:
  ✓ write to factory1
  ✓ write to floor-a and its sensors, brokers, alarms
  ✗ read floor-b (explicit deny)
  ✗ read sensors, alarms under floor-b (deny inherits)
```

### Pattern 5: Dashboard Sharing

```
SETUP:
  alice creates dashboard "my-dash" → auto-granted 'manage'
  alice grants permissions to others:

  resource_permissions:
  ┌─────────────┬──────────────────┬────────┬────────┬────────┐
  │ Grantee     │ Resource         │ Perm   │ Inherit│ Fields │
  ├─────────────┼──────────────────┼────────┼────────┼────────┤
  │ user:alice  │ dashboard:my-dash│ manage │ -      │ null   │ (auto)
  │ user:bob    │ dashboard:my-dash│ read   │ -      │ null   │
  │ group:ops   │ dashboard:my-dash│ write  │ -      │ null   │
  └─────────────┴──────────────────┴────────┴────────┴────────┘

EFFECTIVE:
  alice: full control (manage)
  bob: can view
  ops group members: can view and edit
```

### Pattern 6: System Config Access

```
SETUP:
  RESOURCE_DEFAULTS = {
      'hardware': {'authenticated_read': True, 'admin_only_write': True},
  }
  
  No entries needed in resource_permissions for read access.

EFFECTIVE:
  System admin:
  ✓ read all hardware
  ✓ write all hardware
  ✓ create new hardware
  
  Any authenticated user:
  ✓ read all hardware (via RESOURCE_DEFAULTS)
  ✗ write any hardware
  ✗ create new hardware
```

---

## Business Logic (Not ACL)

### User Self-Update Constraints

This is business logic, handled in use cases, NOT in ACL.

```python
# In user_use_case.py - NOT in ACL service

SELF_UPDATE_RULES = {
    'allowed': ['email', 'password', 'first_name', 'last_name'],
    'forbidden': ['username', 'is_admin', 'disabled'],
}

async def update_user(actor, target_user_id, updates):
    # 1. ACL check
    allowed, fields = await acl.check(actor, 'user', target_user_id, 'write')
    
    if not allowed:
        raise Forbidden("No write permission on user")
    
    # 2. Self-update business rules (separate from ACL)
    if actor.id == target_user_id and not actor.is_admin:
        for field in updates.keys():
            if field in SELF_UPDATE_RULES['forbidden']:
                raise Forbidden(f"Cannot modify {field} on yourself")
    
    # 3. Field-level ACL check (if fields restriction exists)
    if fields is not None:
        for field in updates.keys():
            if field not in fields:
                raise Forbidden(f"Cannot write field: {field}")
    
    # 4. Update allowed
    await db.update('user', target_user_id, updates)
```

---

## API Integration

### Grant Permission

```
POST /api/permissions
{
  "grantee_type": "group",
  "grantee_id": "uuid-operators",
  "resource_type": "site",
  "resource_id": "uuid-factory1",
  "permission": "write",
  "inherit": true,
  "fields": ["field_a", "field_b", "field_c"]
}
```

### Add User to Group (Membership via ACL)

```
POST /api/permissions
{
  "grantee_type": "user",
  "grantee_id": "uuid-alice",
  "resource_type": "group",
  "resource_id": "uuid-f1-admins",
  "permission": "member"
}
```

### Create Resource

```
POST /api/plans
{
  "name": "Floor A",
  "site_id": "uuid-factory1"
}

# Backend:
# 1. Checks 'create' permission on site:factory1
# 2. Creates plan with site_id FK
# 3. Auto-grants 'manage' to creator
```

### Response with Permissions

```json
GET /api/sensors/123

{
  "id": "123",
  "name": "Temperature Sensor",
  "field_a": "value_a",
  "field_b": "value_b",
  "field_c": "value_c",
  "field_d": "value_d",
  "field_e": "value_e",
  "_permissions": {
    "can_read": true,
    "can_write": true,
    "writable_fields": ["field_a", "field_b", "field_c"],
    "can_delete": false,
    "can_manage": false
  }
}
```

---

## Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                        CACHE KEYS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Permission check:                                              │
│  KEY:   perm:{user_id}:{resource_type}:{resource_id}:{perm}     │
│  VALUE: { allowed: bool, fields: list|null }                    │
│  TTL:   300 seconds                                             │
│                                                                 │
│  User groups:                                                   │
│  KEY:   user_groups:{user_id}                                   │
│  VALUE: [group_id, ...]                                         │
│  TTL:   600 seconds                                             │
│                                                                 │
│  Resource ancestors:                                            │
│  KEY:   ancestors:{resource_type}:{resource_id}                 │
│  VALUE: [(type, id, depth), ...]                                │
│  TTL:   3600 seconds (hierarchy rarely changes)                 │
│                                                                 │
│  User admin sites:                                              │
│  KEY:   admin_sites:{user_id}                                   │
│  VALUE: [site_id, ...]                                          │
│  TTL:   600 seconds                                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     INVALIDATION                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  On permission grant/revoke:                                    │
│    DELETE perm:*:{resource_type}:{resource_id}:*                │
│    If inherit=true: DELETE descendant perms too                 │
│                                                                 │
│  On group membership change:                                    │
│    DELETE user_groups:{user_id}                                 │
│    DELETE perm:{user_id}:*                                      │
│    DELETE admin_sites:{user_id}                                 │
│                                                                 │
│  On resource parent change (rare):                              │
│    DELETE ancestors:{resource_type}:{resource_id}               │
│    DELETE perm:*:{resource_type}:{resource_id}:*                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Descendant-Aware Invalidation

```python
def invalidate_permission_cache(resource_type, resource_id, inherit=False):
    """Invalidate permission caches, optionally including children."""
    
    # Clear direct caches
    cache.delete_pattern(f"perm:*:{resource_type}:{resource_id}:*")
    
    if inherit:
        # Get all children and invalidate them too
        children = get_all_descendants(resource_type, resource_id)
        for child_type, child_id in children:
            cache.delete_pattern(f"perm:*:{child_type}:{child_id}:*")


def get_all_descendants(resource_type, resource_id):
    """Get all child resources recursively."""
    # Find child types from hierarchy config
    child_types = [
        t for t, cfg in HIERARCHY_CONFIG.items() 
        if cfg.get('parent_type') == resource_type
    ]
    
    descendants = []
    for child_type in child_types:
        fk = HIERARCHY_CONFIG[child_type]['parent_fk']
        children = db.query(f"""
            SELECT id FROM {child_type}s 
            WHERE {fk} = :parent_id
        """, parent_id=resource_id)
        
        for child in children:
            descendants.append((child_type, child.id))
            descendants.extend(get_all_descendants(child_type, child.id))
    
    return descendants
```

---

## Migration from Old System

### Migrate group.is_admin to Permissions

```python
async def migrate_admin_groups():
    """
    Convert is_admin flag to 'manage' permission.
    Run once during migration.
    """
    admin_groups = await db.query("""
        SELECT id, site_id FROM groups WHERE is_admin = true
    """)
    
    for group in admin_groups:
        if group.site_id:
            # Grant 'manage' on site to this group
            await db.insert('resource_permissions', {
                'grantee_type': 'group',
                'grantee_id': group.id,
                'resource_type': 'site',
                'resource_id': group.site_id,
                'permission': 'manage',
                'effect': 'allow',
                'inherit': True,
                'fields': None,
                'granted_by': None,  # System migration
            })
    
    # After verification, drop is_admin column
    # ALTER TABLE groups DROP COLUMN is_admin;
```

### Migrate group_user_association to Permissions

```python
async def migrate_group_memberships():
    """
    Convert group_user_association to 'member' permissions.
    Run once during migration.
    """
    memberships = await db.query("""
        SELECT user_id, group_id FROM group_user_association
    """)
    
    for m in memberships:
        await db.insert('resource_permissions', {
            'grantee_type': 'user',
            'grantee_id': m.user_id,
            'resource_type': 'group',
            'resource_id': m.group_id,
            'permission': 'member',
            'effect': 'allow',
            'inherit': False,
            'fields': None,
            'granted_by': None,  # System migration
        })
    
    # After verification, drop group_user_association table
    # DROP TABLE group_user_association;
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                   PURE ACL ARCHITECTURE v3                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TABLES:                                                        │
│    Business: users, groups, sites, plans, sensors, brokers,    │
│              alarms, alerts, dashboards, hardware, datatype,   │
│              protocol, parser, manufacturer, communication_mode│
│    ACL: resource_permissions (single table)                    │
│    Association tables: 0 (memberships in ACL)                  │
│    Magic flags: 0 (no is_admin on groups)                      │
│                                                                 │
│  FEATURES:                                                      │
│  ✓ Single table for all permissions                            │
│  ✓ Groups as standalone resources (no hierarchy)               │
│  ✓ Group membership = 'member' permission                      │
│  ✓ Site admin = 'manage' permission (no magic flag)            │
│  ✓ Cross-site groups (permissions on multiple sites)           │
│  ✓ Hybrid inheritance (inherit unless overridden)              │
│  ✓ Field-level access control                                  │
│  ✓ Creator auto-manage                                         │
│  ✓ Permission hierarchy (manage > write > read)                │
│  ✓ Expiring permissions                                        │
│  ✓ Explicit deny overrides                                     │
│  ✓ System config default read (RESOURCE_DEFAULTS)              │
│  ✓ Full audit trail (granted_by, granted_at)                   │
│  ✓ Clear separation (business logic vs ACL)                    │
│                                                                 │
│  HIERARCHY:                                                     │
│    Hierarchical: site → plan → sensor/broker → alarm → alert   │
│    Standalone: group, dashboard, user                          │
│    System config: hardware, datatype, protocol, ...            │
│                                                                 │
│  MIGRATION:                                                     │
│    1. Create resource_permissions table                        │
│    2. Migrate group.is_admin → 'manage' permissions            │
│    3. Migrate group_user_association → 'member' permissions    │
│    4. Drop is_admin column and association table               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
