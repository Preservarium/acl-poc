# Quick Start: Self-Update Business Rules

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependency added: `email-validator==2.1.0`

### 2. Apply Database Migration

```bash
# Run the migration
alembic upgrade head

# Verify migration
alembic current
```

Expected output: `001 (head)`

### 3. Verify Implementation

```bash
# Run unit tests
pytest tests/test_self_update.py -v

# Expected: All tests pass
```

## Quick API Examples

### Setup: Create Test User

```bash
# Start server (in one terminal)
cd backend
uvicorn app.main:app --reload

# In another terminal, create a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login and save token
export TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' \
  | jq -r '.access_token')

# Get your user ID
export USER_ID=$(curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.id')

echo "Token: $TOKEN"
echo "User ID: $USER_ID"
```

### Test 1: Update Allowed Field (Email) ✓

```bash
curl -X PUT http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'

# Expected: 200 OK with updated user
```

### Test 2: Update Allowed Fields (Name) ✓

```bash
curl -X PUT http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe"
  }'

# Expected: 200 OK with updated user
```

### Test 3: Update Forbidden Field (Username) ✗

```bash
curl -X PUT http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "newusername"}'

# Expected: 403 Forbidden
# {"detail": "You cannot modify 'username' on your own account"}
```

### Test 4: Update Forbidden Field (is_admin) ✗

```bash
curl -X PUT http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}'

# Expected: 403 Forbidden
# {"detail": "You cannot modify 'is_admin' on your own account"}
```

### Test 5: Update Forbidden Field (disabled) ✗

```bash
curl -X PUT http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"disabled": true}'

# Expected: 403 Forbidden
# {"detail": "You cannot modify 'disabled' on your own account"}
```

### Test 6: Admin Updates Own Username ✓

```bash
# First create an admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "is_admin": true
  }'

# Login as admin
export ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | jq -r '.access_token')

export ADMIN_ID=$(curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.id')

# Admin can update their own username
curl -X PUT http://localhost:8000/api/users/$ADMIN_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin"}'

# Expected: 200 OK - Admins bypass self-update rules
```

## Business Rules Summary

### Allowed Fields (for non-admin self-updates)
- ✓ email
- ✓ password
- ✓ first_name
- ✓ last_name

### Forbidden Fields (for non-admin self-updates)
- ✗ username
- ✗ is_admin
- ✗ disabled

### Admin Behavior
- ✓ Admins can update ANY field on their own account
- ✓ Admins can update ANY field on ANY other user's account
- ✓ Admins bypass self-update business rules

## Code Usage

### Import and Use Business Rules

```python
from app.core.business_rules import validate_self_update

# In your endpoint
update_data = {'email': 'new@example.com'}

try:
    validate_self_update(update_data, is_admin=current_user.is_admin)
    # Validation passed, proceed with update
except HTTPException as e:
    # Validation failed, return error
    raise e
```

### Get Allowed/Forbidden Fields

```python
from app.core.business_rules import (
    get_allowed_self_update_fields,
    get_forbidden_self_update_fields
)

allowed = get_allowed_self_update_fields()
# ['email', 'password', 'first_name', 'last_name']

forbidden = get_forbidden_self_update_fields()
# ['username', 'is_admin', 'disabled']
```

## Database Schema

### New User Fields

```sql
-- Added by migration 001_add_user_fields.py
ALTER TABLE users ADD COLUMN email VARCHAR(255);
ALTER TABLE users ADD COLUMN first_name VARCHAR(255);
ALTER TABLE users ADD COLUMN last_name VARCHAR(255);
ALTER TABLE users ADD COLUMN disabled BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX ix_users_email ON users(email);
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: Migration fails

**Solution:**
```bash
# Check current migration version
alembic current

# If migration already applied, skip
# If not, apply it
alembic upgrade head

# If you need to rollback
alembic downgrade -1
```

### Issue: Tests fail

**Solution:**
```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests with verbose output
pytest tests/test_self_update.py -vv
```

### Issue: 401 Unauthorized

**Solution:**
- Ensure you're logged in and have a valid token
- Token format should be: `Authorization: Bearer <token>`
- Check token hasn't expired

### Issue: 403 Forbidden (unexpected)

**Debug:**
```bash
# Check if you're modifying the correct user
echo $USER_ID

# Check if field is in forbidden list
# username, is_admin, disabled cannot be self-updated

# Check if you're an admin
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq '.is_admin'
```

## Testing Checklist

- [ ] Dependencies installed (`email-validator` present)
- [ ] Migration applied successfully
- [ ] Unit tests pass (all 10+ tests)
- [ ] Can create user with new fields
- [ ] Can update allowed fields (email, password, first_name, last_name)
- [ ] Cannot update forbidden fields (username, is_admin, disabled)
- [ ] Admins can update all fields
- [ ] Disabled users cannot login
- [ ] ACL permissions still work for cross-user updates

## Next Steps

1. **Run Integration Tests**: Test the full API flow
2. **Update Frontend**: Add UI for new user fields
3. **Add Audit Logging**: Track user updates for compliance
4. **Email Verification**: Verify email addresses when changed
5. **Documentation**: Update API docs with new endpoints

## Files Modified/Created

### Created
- `backend/app/core/business_rules.py` - Business rules module
- `backend/alembic/versions/001_add_user_fields.py` - Database migration
- `backend/tests/test_self_update.py` - Unit tests
- `PHASE1.5_SELF_UPDATE_IMPLEMENTATION.md` - Full documentation
- `docs/self-update-flow.md` - Flow diagrams
- `QUICKSTART_SELF_UPDATE.md` - This file

### Modified
- `backend/app/models/user.py` - Added fields
- `backend/app/schemas/user.py` - Added update schemas
- `backend/app/api/users.py` - Added PUT endpoint
- `backend/app/services/auth_service.py` - Updated for new fields
- `backend/requirements.txt` - Added email-validator

## Support

For issues or questions:
1. Check `/docs/pure-acl-v3.md` for architecture details
2. Review `PHASE1.5_SELF_UPDATE_IMPLEMENTATION.md` for full implementation
3. See `docs/self-update-flow.md` for flow diagrams
