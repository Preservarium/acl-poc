# Group Membership Migration to ACL Table - Summary

## Overview
This migration implements Phase 1.1 of the Pure ACL v3 architecture by moving group membership from the `group_users` association table to the `resource_permissions` table using 'member' permission.

## Changes Made

### 1. Permission Service (`backend/app/services/permission_service.py`)
**Status:** Already implemented correctly

The `get_user_groups()` function (lines 31-58) was already querying from `resource_permissions` where:
- `resource_type = 'group'`
- `permission = 'member'`
- `effect = 'allow'`

This is used throughout the permission checking algorithm to resolve group memberships.

### 2. Group API Endpoints (`backend/app/api/groups.py`)
**Status:** Updated

Modified three endpoints and added two new ones:

#### Updated Endpoints:
- **GET /api/groups**: Modified to count members via `resource_permissions` query instead of using `group.users` relationship
- **GET /api/groups/{group_id}**: Modified to count members via `resource_permissions` query
- **GET /api/groups/{group_id}/members**: Modified to retrieve members by querying `resource_permissions` for 'member' permissions

#### New Endpoints:
- **POST /api/groups/{group_id}/members/{user_id}**: Creates a 'member' permission entry in `resource_permissions` to add a user to a group
- **DELETE /api/groups/{group_id}/members/{user_id}**: Removes the 'member' permission entry to remove a user from a group

All endpoints now:
- Query `resource_permissions` where `permission = 'member'`
- Respect `expires_at` to filter expired memberships
- Check for `effect = 'allow'` to ensure active memberships

### 3. Seed Data (`backend/seed_data.py`)
**Status:** Already implemented correctly

The `seed_permissions()` function (lines 551-607) was already creating group memberships as 'member' permissions in `resource_permissions` instead of using the `group_users` table.

Example from seed data:
```python
{
    "grantee_type": GranteeType.USER,
    "grantee_id": "alice",
    "resource_type": "group",
    "resource_id": "Factory 1 Admins",
    "permission": "member",
    "effect": Effect.ALLOW,
    "inherit": False,
    "fields": None,
}
```

### 4. Alembic Migration (`backend/alembic/versions/002_migrate_group_membership_to_acl.py`)
**Status:** Created

Created a new migration file that:

#### Upgrade:
1. Checks if `group_users` table exists
2. Reads all existing group-user associations from `group_users`
3. For each association, creates a corresponding entry in `resource_permissions`:
   - `grantee_type = 'user'`
   - `grantee_id = user_id`
   - `resource_type = 'group'`
   - `resource_id = group_id`
   - `permission = 'member'`
   - `effect = 'allow'`
   - `inherit = FALSE`
4. Drops the `group_users` table

#### Downgrade:
1. Recreates the `group_users` table with proper foreign keys
2. Reads all 'member' permissions from `resource_permissions`
3. Inserts them back into `group_users`
4. Deletes the 'member' permissions from `resource_permissions`

The migration is idempotent and includes safety checks to avoid duplicate entries.

### 5. Group Model (`backend/app/models/group.py`)
**Status:** Updated

Changes:
- **Removed** the `group_users` Table definition (was lines 9-14)
- **Commented out** the `users` relationship that used `group_users` table (now deprecated)
- **Added** `get_members(db_session)` async method to retrieve members via `resource_permissions`
- Added comprehensive docstrings explaining the migration

The new `get_members()` method:
```python
async def get_members(self, db_session) -> List["User"]:
    """Get all members of this group via resource_permissions."""
    # Queries resource_permissions for 'member' permissions
    # Returns list of User objects
```

### 6. User Model (`backend/app/models/user.py`)
**Status:** Updated

Changes:
- **Commented out** the `groups` relationship that used `group_users` table (now deprecated)
- **Added** `get_groups(db_session)` async method to retrieve groups via `resource_permissions`
- Added comprehensive docstrings explaining the migration

The new `get_groups()` method:
```python
async def get_groups(self, db_session) -> List["Group"]:
    """Get all groups this user is a member of via resource_permissions."""
    # Queries resource_permissions for 'member' permissions
    # Returns list of Group objects
```

## Database Schema Changes

### Before (group_users table):
```sql
CREATE TABLE group_users (
    group_id VARCHAR(36) REFERENCES groups(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, user_id)
);
```

### After (using resource_permissions):
```sql
-- Group membership stored in resource_permissions
SELECT * FROM resource_permissions
WHERE grantee_type = 'user'
  AND resource_type = 'group'
  AND permission = 'member';

-- Example entry:
{
    "id": "uuid",
    "grantee_type": "user",
    "grantee_id": "alice-uuid",
    "resource_type": "group",
    "resource_id": "f1-admins-uuid",
    "permission": "member",
    "effect": "allow",
    "inherit": false,
    "fields": null,
    "granted_by": "admin-uuid",
    "granted_at": "2024-11-26T12:00:00",
    "expires_at": null
}
```

## Benefits of This Migration

1. **Single Source of Truth**: All permissions (including group membership) are now in one table
2. **Consistent Permission Model**: Group membership follows the same pattern as other permissions
3. **Audit Trail**: Track who granted membership and when via `granted_by` and `granted_at`
4. **Expiring Memberships**: Support for temporary group memberships via `expires_at`
5. **Deny Support**: Ability to explicitly deny group membership if needed
6. **Simplified Queries**: Permission resolution algorithm handles both direct permissions and group-based permissions uniformly

## Running the Migration

### To apply the migration:
```bash
cd backend
alembic upgrade head
```

### To rollback (if needed):
```bash
alembic downgrade -1
```

### Fresh database setup:
```bash
# Run migrations
alembic upgrade head

# Seed with test data
python seed_data.py
```

## Testing the Changes

After migration, verify:

1. **List groups with member counts**:
   ```
   GET /api/groups
   ```

2. **Get group members**:
   ```
   GET /api/groups/{group_id}/members
   ```

3. **Add user to group**:
   ```
   POST /api/groups/{group_id}/members/{user_id}
   ```

4. **Remove user from group**:
   ```
   DELETE /api/groups/{group_id}/members/{user_id}
   ```

5. **Verify permission checks work**:
   - Users in "Factory 1 Admins" group should have manage permission on Factory 1 site
   - Users in "Factory 1 Operators" group should have write permission on Factory 1 site
   - Users in "Factory 1 Viewers" group should have read permission on Factory 1 site

## Files Modified

1. `/backend/app/api/groups.py` - Updated API endpoints
2. `/backend/app/models/group.py` - Removed group_users table, added get_members() method
3. `/backend/app/models/user.py` - Deprecated groups relationship, added get_groups() method
4. `/backend/alembic/versions/002_migrate_group_membership_to_acl.py` - New migration file

## Files Already Correct (No Changes Needed)

1. `/backend/app/services/permission_service.py` - Already using resource_permissions
2. `/backend/seed_data.py` - Already creating member permissions

## Backward Compatibility

- The old `users` and `groups` relationships are commented out but not removed
- Migration can be rolled back if needed
- Helper methods (`get_members()`, `get_groups()`) provide the same functionality as the old relationships

## Next Steps

After verifying this migration works correctly:

1. Update any frontend code that might reference the old API patterns
2. Update any tests that rely on the `group_users` table
3. Monitor performance of the new queries
4. Consider adding indexes on `resource_permissions` if needed:
   - `(grantee_type, grantee_id, resource_type)` for member lookups
   - `(resource_type, resource_id, permission)` for resource permission queries

## Compliance with Pure ACL v3 Spec

This migration implements the specification from `docs/pure-acl-v3.md`:

- ✅ Groups are standalone resources (no inheritance)
- ✅ Group membership = 'member' permission on group
- ✅ Membership stored in `resource_permissions` table
- ✅ Supports all permission features (expires_at, granted_by, effect)
- ✅ Permission checking algorithm uses `get_user_groups()` which queries from ACL table
- ✅ Follows the example from lines 606-621 of the spec document
