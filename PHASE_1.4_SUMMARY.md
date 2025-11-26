# Phase 1.4: Add User as Resource Type - Implementation Summary

## Overview
Successfully implemented USER as a permission-grantable resource type, allowing permissions to be granted on user resources (e.g., allowing certain users to manage other users).

## Changes Made

### Backend Changes

#### 1. Model Updates (`backend/app/models/permission.py`)
- Added `USER = "user"` to the `ResourceType` enum
- Users can now be treated as resources in the permission system

#### 2. Schema Updates (`backend/app/schemas/permission.py`)
- Added `GROUP = "group"` and `USER = "user"` to the `ResourceType` enum in schemas
- Ensures API validation accepts user and group as valid resource types

#### 3. Hierarchy Configuration (`backend/app/services/hierarchy.py`)
- Added user to `HIERARCHY_CONFIG` as a standalone resource:
  ```python
  'user': {'parent_type': None, 'parent_fk': None}
  ```
- Updated `get_model_class()` to include User model mapping
- Users are now treated as standalone resources with no parent hierarchy

#### 4. Permission Service (`backend/app/services/permission_service.py`)
- No changes needed - the service already handles all resource types dynamically
- Permission checks work automatically for user resource type
- Inheritance logic correctly treats users as standalone (no inheritance)

#### 5. Permissions API (`backend/app/api/permissions.py`)
- Updated `get_resource_name()` to handle 'user' resource type:
  - Returns username when resource_type is 'user'
- Updated `get_resource_name()` to handle 'group' resource type:
  - Returns group name when resource_type is 'group'
- Added validation in `grant_permission()` endpoint:
  - Verifies target user exists when granting permissions on user resources
  - Verifies target group exists when granting permissions on group resources

#### 6. Users API (`backend/app/api/users.py`)
- Added new endpoint: `GET /api/users/{user_id}/permissions`
  - Returns all permissions granted ON a specific user
  - Requires admin or 'manage' permission on the user
  - Shows who can manage/access that user

- Added new endpoint: `POST /api/users/{user_id}/permissions`
  - Grants permission on a user to another user/group
  - Requires admin or 'manage' permission on the target user
  - Validates that grantee (user/group) exists
  - Automatically sets resource_type to 'user' and resource_id to the target user

### Frontend Changes

#### 7. Type Definitions (`frontend/src/types.ts`)
- Updated `ResourceType` to include 'user':
  ```typescript
  export type ResourceType = 'group' | 'user' | 'site' | 'plan' | 'sensor' | 'broker' | 'alarm' | 'alert' | 'dashboard'
  ```

#### 8. Type Definitions (`frontend/src/types/index.ts`)
- Updated `ResourceType` to include 'user':
  ```typescript
  export type ResourceType = 'site' | 'plan' | 'sensor' | 'alarm' | 'alert' | 'broker' | 'dashboard' | 'group' | 'user'
  ```

## API Endpoints Added

### Get User Permissions
```
GET /api/users/{user_id}/permissions
```
Returns list of permissions granted ON this user.

**Authorization:**
- Admins can always access
- Users with 'manage' permission on the target user
- Users can view their own permissions

**Response:**
```json
[
  {
    "id": "perm-id",
    "grantee_type": "user",
    "grantee_id": "alice-id",
    "grantee_name": "alice",
    "resource_type": "user",
    "resource_id": "bob-id",
    "resource_name": "bob",
    "permission": "manage",
    "effect": "allow",
    "inherit": true,
    "granted_by": "admin-id",
    "granted_at": "2025-01-15T10:00:00"
  }
]
```

### Grant User Permission
```
POST /api/users/{user_id}/permissions
```
Grants permission on a user to another user/group.

**Authorization:**
- Admins can always grant
- Users with 'manage' permission on the target user

**Request Body:**
```json
{
  "grantee_type": "user",
  "grantee_id": "alice-id",
  "permission": "manage",
  "effect": "allow",
  "inherit": true
}
```

**Note:** `resource_type` and `resource_id` are automatically set to 'user' and the target user ID.

## Example Use Cases

### 1. Grant Alice permission to manage Bob's account
```python
await permission_service.grant(
    grantee_type='user',
    grantee_id=alice.id,
    resource_type='user',
    resource_id=bob.id,
    permission='manage'
)
```

### 2. Check if Alice can write to Bob's user record
```python
allowed, fields = await permission_service.check(
    user_id=alice.id,
    resource_type='user',
    resource_id=bob.id,
    permission='write'
)
```

### 3. Grant HR group read access to all employees
```python
for employee in employees:
    await permission_service.grant(
        grantee_type='group',
        grantee_id=hr_group.id,
        resource_type='user',
        resource_id=employee.id,
        permission='read'
    )
```

### 4. Allow managers to manage their team members
```python
for team_member in team_members:
    await permission_service.grant(
        grantee_type='user',
        grantee_id=manager.id,
        resource_type='user',
        resource_id=team_member.id,
        permission='manage'
    )
```

## Integration with Existing User Update Endpoint

The existing `PUT /api/users/{user_id}` endpoint already uses the permission system:

```python
# Check if user has 'write' permission on target user
allowed, fields = await permission_service.check(
    current_user,
    ResourceType.USER,
    user_id,
    Permission.WRITE
)
```

This means:
- Users can update other users if they have 'write' permission on the user resource
- Field-level permissions are enforced
- Self-update business rules still apply (non-admins can't change their own admin status)

## Resource Hierarchy

Users are **standalone resources** (no parent hierarchy):
- Permissions granted on a user apply only to that user
- No inheritance up or down (users have no parent or children in the resource tree)
- Similar to groups and dashboards in this respect

## Files Modified

### Backend
1. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/backend/app/models/permission.py`
2. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/backend/app/schemas/permission.py`
3. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/backend/app/services/hierarchy.py`
4. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/backend/app/api/permissions.py`
5. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/backend/app/api/users.py`

### Frontend
6. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/frontend/src/types.ts`
7. `/Users/andymonga/Projects/PreservariumV3/main/acl-poc/frontend/src/types/index.ts`

## Testing Recommendations

To test the implementation:

1. **Grant permission on a user:**
   ```bash
   POST /api/users/{bob_id}/permissions
   {
     "grantee_type": "user",
     "grantee_id": "{alice_id}",
     "permission": "manage"
   }
   ```

2. **List permissions on a user:**
   ```bash
   GET /api/users/{bob_id}/permissions
   ```

3. **Check permission (using existing endpoint):**
   ```bash
   POST /api/permissions/check
   {
     "checks": [
       {
         "resource_type": "user",
         "resource_id": "{bob_id}",
         "permission": "write"
       }
     ]
   }
   ```

4. **Update a user (existing endpoint, now with ACL):**
   ```bash
   PUT /api/users/{bob_id}
   {
     "email": "newemail@example.com"
   }
   ```
   - This will check if the current user has 'write' permission on bob

## Notes

- Admin users bypass all permission checks (can always manage all users)
- Users can always view their own permissions
- The permission system is fully integrated with the existing user management
- Field-level permissions work on user resources (can restrict which fields can be modified)
- Users are treated as standalone resources (no hierarchical inheritance)

## Completion Status

All tasks completed:
- ✅ Updated ResourceType enum with USER
- ✅ Updated HIERARCHY_CONFIG to include user as standalone resource
- ✅ Added user to model class mapping
- ✅ Updated permission validation to accept user resource type
- ✅ Added resource existence validation for user and group
- ✅ Added user permissions API endpoints (GET and POST)
- ✅ Updated frontend TypeScript types
- ✅ Verified integration with existing user update endpoint
