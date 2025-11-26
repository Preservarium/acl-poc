# Phase 1.5: Self-Update Business Rules Implementation

## Overview

This document summarizes the implementation of self-update business rules as specified in `docs/pure-acl-v3.md`. The implementation restricts what fields a non-admin user can modify on their own account.

## Business Rules Implemented

```python
SELF_UPDATE_RULES = {
    'allowed': ['email', 'password', 'first_name', 'last_name'],
    'forbidden': ['username', 'is_admin', 'disabled'],
}
```

**Rule:** A non-admin user cannot modify their own `username`, `is_admin`, or `disabled` fields.

**Behavior:**
- Regular users can update: email, password, first_name, last_name (on themselves)
- Regular users cannot update: username, is_admin, disabled (on themselves)
- Admins can update any field (including on themselves)
- ACL permissions still apply when updating other users

## Files Created

### 1. `/backend/app/core/business_rules.py` (NEW)

**Purpose:** Central module for business logic and validation rules separate from ACL.

**Key Functions:**
- `validate_self_update(updates, is_admin)`: Validates self-update attempts against SELF_UPDATE_RULES
- `get_allowed_self_update_fields()`: Returns list of allowed fields for self-updates
- `get_forbidden_self_update_fields()`: Returns list of forbidden fields for self-updates

**Usage Example:**
```python
from app.core.business_rules import validate_self_update

# This will raise HTTPException 403
validate_self_update({'username': 'newname'}, is_admin=False)

# This will pass
validate_self_update({'email': 'new@example.com'}, is_admin=False)

# Admins can do anything
validate_self_update({'username': 'newname'}, is_admin=True)
```

### 2. `/backend/alembic/versions/001_add_user_fields.py` (NEW)

**Purpose:** Database migration to add new user fields.

**Changes:**
- Adds `email` column (String(255), nullable, indexed)
- Adds `first_name` column (String(255), nullable)
- Adds `last_name` column (String(255), nullable)
- Adds `disabled` column (Boolean, not null, default false)

**Migration Commands:**
```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 3. `/backend/tests/test_self_update.py` (NEW)

**Purpose:** Unit tests for self-update business rules.

**Test Coverage:**
- Allowed fields validation
- Forbidden fields rejection
- Admin bypass behavior
- Mixed allowed/forbidden fields
- Empty updates handling

**Run Tests:**
```bash
pytest backend/tests/test_self_update.py -v
```

## Files Modified

### 1. `/backend/app/models/user.py`

**Changes:**
- Added `email` field (String(255), indexed, nullable)
- Added `first_name` field (String(255), nullable)
- Added `last_name` field (String(255), nullable)
- Added `disabled` field (Boolean, default False)

**Note:** The model was already modified by the linter to use the new permission-based group membership system.

### 2. `/backend/app/schemas/user.py`

**New Schemas:**

#### `UserUpdate`
Used for self-updates by non-admin users. Contains only allowed fields:
- email (EmailStr, optional)
- password (string, optional, min_length=6)
- first_name (string, optional)
- last_name (string, optional)

#### `UserAdminUpdate`
Extends `UserUpdate` with privileged fields for admin operations:
- username (string, optional, min_length=3)
- is_admin (boolean, optional)
- disabled (boolean, optional)

**Modified Schemas:**
- `UserCreate`: Added email, first_name, last_name fields
- `UserResponse`: Added email, first_name, last_name, disabled fields

### 3. `/backend/app/api/users.py`

**New Endpoint:**

#### `PUT /users/{user_id}`
Updates a user's information with proper validation.

**Logic Flow:**
1. Fetch target user from database
2. Parse update data (exclude unset fields)
3. Check if this is a self-update (current_user.id == user_id)
4. **If self-update:**
   - Apply `validate_self_update()` business rule
   - Admins bypass this check
5. **If updating another user:**
   - Check ACL permission (need 'write' on user resource)
   - Validate field-level restrictions if ACL specifies fields
6. Hash password if being updated
7. Apply updates and save

**Request Example:**
```bash
# User updates their own email (allowed)
curl -X PUT http://localhost:8000/api/users/{id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'

# User tries to update own username (forbidden - will fail)
curl -X PUT http://localhost:8000/api/users/{id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"username": "newusername"}'
# Response: 403 Forbidden - "You cannot modify 'username' on your own account"

# Admin updates own username (allowed)
curl -X PUT http://localhost:8000/api/users/{id} \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"username": "newusername"}'
```

### 4. `/backend/app/services/auth_service.py`

**Changes:**

#### `create_user()` method
Added optional parameters for new user fields:
- email (optional)
- first_name (optional)
- last_name (optional)

#### `authenticate_user()` method
Added check for `disabled` field:
- Users with `disabled=True` cannot authenticate
- Returns None if user is disabled (same as wrong password)

### 5. `/backend/requirements.txt`

**Addition:**
- `email-validator==2.1.0` (required for Pydantic's EmailStr)

## Architecture Principles

This implementation follows the separation of concerns outlined in `docs/pure-acl-v3.md`:

```
┌─────────────────────────────────────────────────────────────────┐
│   BUSINESS LAYER                    ACL LAYER                   │
│   (Data & Relationships)            (Access Control)            │
│                                                                  │
│   Self-update constraints    ←→     Permission checks           │
│   (business_rules.py)               (permission_service.py)     │
│   - Who can modify what             - Who has access            │
│   - Field validation                - Field restrictions        │
│   - Domain rules                    - Inheritance logic         │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
1. **Self-update rules are business logic**, not ACL
2. **ACL handles "can I access this resource?"**
3. **Business rules handle "what can I do with this resource?"**
4. **Both checks must pass** for an operation to succeed

## Permission Flow for User Updates

### Scenario 1: User updates their own email
```
1. User makes PUT /users/{their_id} with {email: "new@example.com"}
2. Check: is_self_update = True
3. Apply: validate_self_update() → PASS (email is allowed)
4. Update database
5. Return 200 OK
```

### Scenario 2: User tries to update their own username
```
1. User makes PUT /users/{their_id} with {username: "newname"}
2. Check: is_self_update = True
3. Apply: validate_self_update() → FAIL (username is forbidden)
4. Return 403 Forbidden: "You cannot modify 'username' on your own account"
```

### Scenario 3: Admin updates their own username
```
1. Admin makes PUT /users/{their_id} with {username: "newname"}
2. Check: is_self_update = True
3. Apply: validate_self_update(is_admin=True) → PASS (admins bypass)
4. Update database
5. Return 200 OK
```

### Scenario 4: User A updates User B (with permission)
```
1. User A makes PUT /users/{user_b_id} with {email: "new@example.com"}
2. Check: is_self_update = False
3. Apply: ACL check → User A has 'write' permission on User B → PASS
4. Check: fields restriction → No field restrictions or email in allowed fields → PASS
5. Update database
6. Return 200 OK
```

### Scenario 5: User A updates User B (without permission)
```
1. User A makes PUT /users/{user_b_id} with {email: "new@example.com"}
2. Check: is_self_update = False
3. Apply: ACL check → User A has NO 'write' permission on User B → FAIL
4. Return 403 Forbidden: "You don't have permission to modify this user"
```

## Testing Instructions

### 1. Apply Database Migration

```bash
cd backend
alembic upgrade head
```

### 2. Run Unit Tests

```bash
# Run all self-update tests
pytest tests/test_self_update.py -v

# Run specific test
pytest tests/test_self_update.py::TestSelfUpdateRules::test_self_update_forbidden_username -v
```

### 3. Manual API Testing

```bash
# Start the backend server
uvicorn app.main:app --reload

# Create a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' \
  | jq -r '.access_token')

# Test allowed update (should succeed)
curl -X PUT http://localhost:8000/api/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com", "first_name": "Test"}'

# Test forbidden update (should fail with 403)
curl -X PUT http://localhost:8000/api/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "newusername"}'
```

## Security Considerations

1. **Password Hashing**: Passwords are hashed using bcrypt before storage
2. **Admin Bypass**: System admins (is_admin=True) can modify any field
3. **Disabled Users**: Users with disabled=True cannot authenticate
4. **Field Validation**: Pydantic schemas validate all input data
5. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
6. **Token Authentication**: JWT tokens required for all updates

## Future Enhancements

Potential improvements for future phases:

1. **Audit Logging**: Log all user updates for compliance
2. **Email Verification**: Require email verification when email is changed
3. **Password History**: Prevent reuse of recent passwords
4. **Rate Limiting**: Limit update frequency to prevent abuse
5. **Field History**: Track changes to sensitive fields
6. **Notification**: Email users when their account is modified
7. **Two-Factor Auth**: Require 2FA for sensitive field changes

## Compatibility Notes

- **Python**: Requires Python 3.10+ (for modern type hints)
- **Pydantic**: v2.5.3+ (for EmailStr support)
- **SQLAlchemy**: v2.0+ (async support)
- **FastAPI**: v0.109.0+

## Summary

The self-update business rules implementation successfully enforces field-level restrictions on user accounts while maintaining separation from the ACL system. Non-admin users are prevented from modifying privileged fields (username, is_admin, disabled) on their own accounts, while admins retain full control. The implementation integrates seamlessly with the existing ACL permission system for cross-user updates.

**Key Deliverables:**
✅ Business rules module with SELF_UPDATE_RULES
✅ Database migration for new user fields
✅ Updated user schemas with proper validation
✅ User update API endpoint with dual validation (business rules + ACL)
✅ Enhanced auth service with new field support
✅ Unit tests for business rule validation
✅ Comprehensive documentation

**Next Steps:**
- Apply database migration: `alembic upgrade head`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `pytest tests/test_self_update.py -v`
- Test API endpoints manually or via integration tests
