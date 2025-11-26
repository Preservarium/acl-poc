# Permission Hierarchy Quick Reference

## Overview

The ACL system implements a permission hierarchy where higher permissions automatically grant lower permissions. This means granting a user `manage` permission also gives them `create`, `delete`, `write`, and `read` capabilities.

## Hierarchy Diagram

```
            manage
           /  |  |  \
          /   |  |   \
         /    |   \   \
    create  delete write
         \    |    /
          \   |   /
            read
```

## Permission Implications

### Checking READ
When checking if a user can `read`, the system accepts ANY of these permissions:
- `read` ✓
- `write` ✓ (implies read)
- `delete` ✓ (implies read)
- `create` ✓ (implies read)
- `manage` ✓ (implies read)

### Checking WRITE
When checking if a user can `write`, the system accepts:
- `write` ✓
- `manage` ✓ (implies write)

### Checking DELETE
When checking if a user can `delete`, the system accepts:
- `delete` ✓
- `manage` ✓ (implies delete)

### Checking CREATE
When checking if a user can `create`, the system accepts:
- `create` ✓
- `manage` ✓ (implies create)

### Checking MANAGE
When checking if a user can `manage`, the system accepts:
- `manage` ✓ (only)

## Permission Matrix

| User Has  | Can READ | Can WRITE | Can DELETE | Can CREATE | Can MANAGE |
|-----------|----------|-----------|------------|------------|------------|
| read      | ✅       | ❌        | ❌         | ❌         | ❌         |
| write     | ✅       | ✅        | ❌         | ❌         | ❌         |
| delete    | ✅       | ❌        | ✅         | ❌         | ❌         |
| create    | ✅       | ❌        | ❌         | ✅         | ❌         |
| manage    | ✅       | ✅        | ✅         | ✅         | ✅         |

## Code Reference

### PERMISSION_HIERARCHY Constant

```python
PERMISSION_HIERARCHY = {
    Permission.READ: [
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.CREATE,
        Permission.MANAGE
    ],
    Permission.WRITE: [
        Permission.WRITE,
        Permission.MANAGE
    ],
    Permission.DELETE: [
        Permission.DELETE,
        Permission.MANAGE
    ],
    Permission.CREATE: [
        Permission.CREATE,
        Permission.MANAGE
    ],
    Permission.MANAGE: [
        Permission.MANAGE
    ],
}
```

### expand_permission() Function

```python
def expand_permission(permission: Permission) -> List[Permission]:
    """
    Expand a permission to include all permissions that imply it.

    Example:
        >>> expand_permission(Permission.READ)
        [Permission.READ, Permission.WRITE, Permission.DELETE,
         Permission.CREATE, Permission.MANAGE]
    """
    return PERMISSION_HIERARCHY.get(permission, [permission])
```

## Usage Examples

### Example 1: Grant MANAGE, Check READ

```python
# Grant manage permission
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.MANAGE,
)

# Check read permission
allowed, fields = await permission_service.check(
    user=user,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.READ,
)

# Result: allowed=True ✅
# Reason: manage implies read
```

### Example 2: Grant WRITE, Check MANAGE

```python
# Grant write permission
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.WRITE,
)

# Check manage permission
allowed, fields = await permission_service.check(
    user=user,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.MANAGE,
)

# Result: allowed=False ❌
# Reason: write does NOT imply manage
```

### Example 3: Grant READ, Check WRITE

```python
# Grant read permission
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.READ,
)

# Check write permission
allowed, fields = await permission_service.check(
    user=user,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.WRITE,
)

# Result: allowed=False ❌
# Reason: read does NOT imply write
```

### Example 4: Multiple Permissions via Group

```python
# User is member of admin group
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.GROUP,
    resource_id=admin_group.id,
    permission=Permission.MEMBER,
)

# Admin group has manage on site
await permission_service.grant(
    grantee_type=GranteeType.GROUP,
    grantee_id=admin_group.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.MANAGE,
)

# Check any permission on site
for perm in [Permission.READ, Permission.WRITE, Permission.DELETE,
             Permission.CREATE, Permission.MANAGE]:
    allowed, _ = await permission_service.check(
        user=user,
        resource_type=ResourceType.SITE,
        resource_id=site.id,
        permission=perm,
    )
    # Result: allowed=True for ALL ✅
    # Reason: User is in group with manage, which implies all
```

## Combined with Resource Hierarchy

The permission hierarchy works seamlessly with resource inheritance:

```python
# Grant manage on site (with inherit=True)
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.MANAGE,
    inherit=True,  # ← Permissions inherit to children
)

# Check read on child sensor
allowed, _ = await permission_service.check(
    user=user,
    resource_type=ResourceType.SENSOR,
    resource_id=sensor.id,  # sensor.plan.site == site
    permission=Permission.READ,
)

# Result: allowed=True ✅
# Reason:
#   1. User has manage on site
#   2. manage inherits to plan, then to sensor
#   3. manage implies read
```

## Field-Level Restrictions

Field restrictions are preserved through the hierarchy:

```python
# Grant manage with field restriction
await permission_service.grant(
    grantee_type=GranteeType.USER,
    grantee_id=user.id,
    resource_type=ResourceType.SENSOR,
    resource_id=sensor.id,
    permission=Permission.MANAGE,
    fields=['field_a', 'field_b'],  # ← Restricted to specific fields
)

# Check read (implied by manage)
allowed, fields = await permission_service.check(
    user=user,
    resource_type=ResourceType.SENSOR,
    resource_id=sensor.id,
    permission=Permission.READ,
)

# Result:
#   allowed=True ✅
#   fields=['field_a', 'field_b']  # Same field restriction applies
```

## Best Practices

### 1. Grant the Minimum Required Permission

```python
# ❌ Bad: Granting manage when only read is needed
await permission_service.grant(
    permission=Permission.MANAGE,  # Overkill!
)

# ✅ Good: Grant only what's needed
await permission_service.grant(
    permission=Permission.READ,  # Just right
)
```

### 2. Use MANAGE for Administrative Roles

```python
# ✅ Good: Site admins get manage
await permission_service.grant(
    grantee_type=GranteeType.GROUP,
    grantee_id=site_admins_group.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.MANAGE,  # ← Full control
    inherit=True,  # ← Applies to all children
)
```

### 3. Use Field Restrictions When Needed

```python
# ✅ Good: Operators can write some fields, read all
await permission_service.grant(
    grantee_type=GranteeType.GROUP,
    grantee_id=operators_group.id,
    resource_type=ResourceType.SENSOR,
    resource_id=sensor.id,
    permission=Permission.WRITE,
    fields=['field_a', 'field_b'],  # Can only write these
)

# Result: They can:
#   - Read all fields (write implies read, no field restriction on read)
#   - Write field_a and field_b only
```

### 4. Leverage Inheritance for Efficiency

```python
# ✅ Good: Single permission on site covers all children
await permission_service.grant(
    grantee_type=GranteeType.GROUP,
    grantee_id=viewers_group.id,
    resource_type=ResourceType.SITE,
    resource_id=site.id,
    permission=Permission.READ,
    inherit=True,  # ← All plans, sensors, etc. covered
)

# ❌ Bad: Granting on every resource individually
# (Inefficient and hard to manage)
```

## Testing

See `test_permission_hierarchy.py` for comprehensive test cases covering all hierarchy scenarios.

## Implementation Details

For implementation details, see:
- `backend/app/services/permission_service.py` - Main implementation
- `backend/app/models/permission.py` - Permission enum definitions
- `IMPLEMENTATION_SUMMARY.md` - Full implementation documentation
