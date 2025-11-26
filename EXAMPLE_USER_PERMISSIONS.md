# Example: User Permissions Usage

This document demonstrates how to use the new user-as-resource permission system.

## Scenario: Team Lead Managing Team Members

Alice is a team lead who needs to manage her team members (Bob and Carol).

### Step 1: Grant Alice permission to manage Bob

As an admin, grant Alice 'manage' permission on Bob's user account:

```bash
curl -X POST http://localhost:8000/api/users/{bob_id}/permissions \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "grantee_type": "user",
    "grantee_id": "{alice_id}",
    "permission": "manage",
    "effect": "allow",
    "inherit": true
  }'
```

**Response:**
```json
{
  "id": "perm-uuid",
  "grantee_type": "user",
  "grantee_id": "{alice_id}",
  "grantee_name": "alice",
  "resource_type": "user",
  "resource_id": "{bob_id}",
  "resource_name": "bob",
  "permission": "manage",
  "effect": "allow",
  "inherit": true,
  "granted_by": "{admin_id}",
  "granted_at": "2025-01-15T10:00:00"
}
```

### Step 2: Alice can now manage Bob's account

Alice can update Bob's user information:

```bash
curl -X PUT http://localhost:8000/api/users/{bob_id} \
  -H "Authorization: Bearer {alice_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob.new@company.com",
    "disabled": false
  }'
```

This works because:
1. Alice has 'manage' permission on Bob (user resource)
2. 'manage' implies 'write', 'read', 'delete', and 'create'
3. The existing user update endpoint checks for 'write' permission

### Step 3: Grant HR group read access to all team members

As an admin, grant the HR group read permission on Bob:

```bash
curl -X POST http://localhost:8000/api/users/{bob_id}/permissions \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "grantee_type": "group",
    "grantee_id": "{hr_group_id}",
    "permission": "read",
    "effect": "allow",
    "inherit": true
  }'
```

Now anyone in the HR group can view Bob's user information.

### Step 4: View who has permissions on Bob

Check all permissions granted on Bob's user account:

```bash
curl -X GET http://localhost:8000/api/users/{bob_id}/permissions \
  -H "Authorization: Bearer {admin_token}"
```

**Response:**
```json
[
  {
    "id": "perm-1",
    "grantee_type": "user",
    "grantee_id": "{alice_id}",
    "grantee_name": "alice",
    "resource_type": "user",
    "resource_id": "{bob_id}",
    "resource_name": "bob",
    "permission": "manage",
    "effect": "allow",
    "inherit": true,
    "granted_by": "{admin_id}",
    "granted_at": "2025-01-15T10:00:00"
  },
  {
    "id": "perm-2",
    "grantee_type": "group",
    "grantee_id": "{hr_group_id}",
    "grantee_name": "HR",
    "resource_type": "user",
    "resource_id": "{bob_id}",
    "resource_name": "bob",
    "permission": "read",
    "effect": "allow",
    "inherit": true,
    "granted_by": "{admin_id}",
    "granted_at": "2025-01-15T10:05:00"
  }
]
```

### Step 5: Check if a user can perform an action

Check if Alice can write to Bob's account:

```bash
curl -X POST http://localhost:8000/api/permissions/check \
  -H "Authorization: Bearer {alice_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "checks": [
      {
        "resource_type": "user",
        "resource_id": "{bob_id}",
        "permission": "write"
      }
    ]
  }'
```

**Response:**
```json
{
  "results": [
    {
      "resource_type": "user",
      "resource_id": "{bob_id}",
      "permission": "write",
      "allowed": true
    }
  ]
}
```

## Scenario: Department Managers

Grant all managers in the "Managers" group the ability to view all users in the system.

### Step 1: Create a script to grant read permission

```python
# Python example using the API
import httpx

async def grant_managers_user_access():
    admin_token = "admin-jwt-token"
    managers_group_id = "managers-group-id"

    # Get all users
    async with httpx.AsyncClient() as client:
        users_response = await client.get(
            "http://localhost:8000/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        users = users_response.json()

        # Grant managers group read permission on each user
        for user in users:
            await client.post(
                f"http://localhost:8000/api/users/{user['id']}/permissions",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "grantee_type": "group",
                    "grantee_id": managers_group_id,
                    "permission": "read",
                    "effect": "allow",
                    "inherit": true
                }
            )
```

## Scenario: Self-Service with Restrictions

Allow users to update their own profile, but restrict which fields they can modify.

### Step 1: Grant user write permission with field restrictions

```bash
curl -X POST http://localhost:8000/api/users/{bob_id}/permissions \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "grantee_type": "user",
    "grantee_id": "{bob_id}",
    "permission": "write",
    "effect": "allow",
    "inherit": true,
    "fields": ["email", "password"]
  }'
```

Now Bob can only update his email and password, not other fields like `is_admin` or `disabled`.

## Permission Hierarchy

Remember that permissions have a hierarchy:
- `manage` implies: `read`, `write`, `delete`, `create`
- `write` does not imply `read` (they are separate)
- `create` allows creating new sub-resources (not applicable to user resources)

## Important Notes

1. **Admin Bypass**: Admin users bypass all permission checks
2. **Self-Update Rules**: Non-admin users cannot change their own `is_admin`, `disabled`, or `username` fields (business rule enforced separately)
3. **Standalone Resource**: Users have no parent in the hierarchy, so permissions don't inherit up or down
4. **Field-Level Permissions**: You can restrict permissions to specific fields using the `fields` parameter
5. **Permission Precedence**: DENY effects take precedence over ALLOW effects

## Integration with Existing Endpoints

The user permissions integrate seamlessly with existing endpoints:

- `GET /api/users` - Returns all users (no permission check)
- `GET /api/users/{user_id}` - Returns specific user (no permission check currently)
- `PUT /api/users/{user_id}` - Updates user (checks 'write' permission on user resource)
- `GET /api/users/{user_id}/permissions` - Lists permissions on user (NEW)
- `POST /api/users/{user_id}/permissions` - Grants permission on user (NEW)

## Error Handling

### 403 Forbidden
```json
{
  "detail": "You don't have permission to grant permissions on this user"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

or

```json
{
  "detail": "Grantee user not found"
}
```

## Testing the Implementation

Use the following curl commands to test:

```bash
# 1. Login as admin
ADMIN_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')

# 2. Create test users
ALICE_ID=$(curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password"}' | jq -r '.id')

BOB_ID=$(curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "password"}' | jq -r '.id')

# 3. Grant Alice permission to manage Bob
curl -X POST "http://localhost:8000/api/users/${BOB_ID}/permissions" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"grantee_type\": \"user\",
    \"grantee_id\": \"${ALICE_ID}\",
    \"permission\": \"manage\"
  }"

# 4. List permissions on Bob
curl -X GET "http://localhost:8000/api/users/${BOB_ID}/permissions" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# 5. Login as Alice
ALICE_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password"}' | jq -r '.access_token')

# 6. Alice updates Bob's email
curl -X PUT "http://localhost:8000/api/users/${BOB_ID}" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"email": "bob.new@example.com"}'
```
