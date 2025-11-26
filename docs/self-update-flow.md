# Self-Update Business Rules Flow Diagram

## Update Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PUT /users/{user_id}                            │
│                  {field: value, ...}                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  Get Target User   │
                │   from Database    │
                └─────────┬──────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  user_id == current │ NO   ┌──────────────────────┐
                │    user.id?         ├─────▶│  Cross-User Update   │
                │  (Self-Update?)     │      │  Check ACL Perms     │
                └─────────┬───────────┘      └──────────┬───────────┘
                          │                              │
                         YES                             │
                          │                              ▼
                          │                   ┌──────────────────────┐
                          │                   │ Has 'write' on user? │
                          │                   └──────────┬───────────┘
                          │                              │
                          │                         ┌────┴─────┐
                          │                        YES         NO
                          │                         │           │
                          ▼                         ▼           ▼
         ┌─────────────────────────────┐   ┌─────────────┐  ┌────────┐
         │  Check Business Rules       │   │  Check      │  │  403   │
         │  validate_self_update()     │   │  Fields     │  │Forbidden│
         └─────────┬───────────────────┘   └──────┬──────┘  └────────┘
                   │                              │
              ┌────┴─────┐                       │
             YES         NO                      │
              │           │                       │
              │           ▼                       │
              │      ┌────────┐                  │
              │      │  403   │                  │
              │      │Forbidden│                  │
              │      └────────┘                  │
              │                                   │
              └───────────────┬───────────────────┘
                              │
                              ▼
                     ┌────────────────────┐
                     │  Hash Password     │
                     │  (if present)      │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │  Apply Updates     │
                     │  to User Object    │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │  Save to Database  │
                     │  db.commit()       │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │  Return 200 OK     │
                     │  Updated User      │
                     └────────────────────┘
```

## Self-Update Business Rule Logic

```
┌──────────────────────────────────────────────────────────────────┐
│            validate_self_update(updates, is_admin)               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  is_admin?   │ YES ────▶ RETURN (bypass check)
                  └──────┬───────┘
                        NO
                         │
                         ▼
          ┌──────────────────────────────────┐
          │  For each field in updates:      │
          │                                   │
          │  ALLOWED = ['email', 'password',  │
          │             'first_name',         │
          │             'last_name']          │
          │                                   │
          │  FORBIDDEN = ['username',         │
          │              'is_admin',          │
          │              'disabled']          │
          └───────────────┬──────────────────┘
                          │
                          ▼
           ┌──────────────────────────────┐
           │  field in FORBIDDEN?         │
           └─────────┬────────────────────┘
                     │
                ┌────┴─────┐
               YES         NO
                │           │
                ▼           ▼
          ┌──────────┐   ┌──────────┐
          │  RAISE   │   │ Continue │
          │  403     │   │ to next  │
          │ Forbidden│   │  field   │
          └──────────┘   └──────┬───┘
                                 │
                                 ▼
                          ┌────────────┐
                          │ All fields │
                          │  checked?  │
                          └──────┬─────┘
                                 │
                                YES
                                 │
                                 ▼
                            ┌─────────┐
                            │ RETURN  │
                            │(success)│
                            └─────────┘
```

## Example Scenarios

### Scenario 1: User Updates Own Email (✓ Allowed)

```
User: testuser (is_admin=False)
Request: PUT /users/{testuser_id}
Body: {"email": "new@example.com"}

Flow:
1. is_self_update = True
2. validate_self_update({'email': 'new@...'}, is_admin=False)
3. 'email' in ALLOWED ✓
4. Update succeeds
5. Return 200 OK
```

### Scenario 2: User Updates Own Username (✗ Forbidden)

```
User: testuser (is_admin=False)
Request: PUT /users/{testuser_id}
Body: {"username": "newname"}

Flow:
1. is_self_update = True
2. validate_self_update({'username': 'newname'}, is_admin=False)
3. 'username' in FORBIDDEN ✗
4. Raise HTTPException(403, "You cannot modify 'username' on your own account")
5. Return 403 Forbidden
```

### Scenario 3: Admin Updates Own Username (✓ Allowed)

```
User: admin (is_admin=True)
Request: PUT /users/{admin_id}
Body: {"username": "newadmin"}

Flow:
1. is_self_update = True
2. validate_self_update({'username': 'newadmin'}, is_admin=True)
3. is_admin=True → BYPASS all checks ✓
4. Update succeeds
5. Return 200 OK
```

### Scenario 4: User A Updates User B with Permission (✓ Allowed)

```
User A: manager (is_admin=False)
User B: employee
Permissions: User A has 'write' permission on User B
Request: PUT /users/{employee_id}
Body: {"email": "employee@example.com"}

Flow:
1. is_self_update = False
2. Check ACL: manager has 'write' on employee ✓
3. No self-update rules apply (different user)
4. Update succeeds
5. Return 200 OK
```

### Scenario 5: User A Updates User B without Permission (✗ Forbidden)

```
User A: employee1 (is_admin=False)
User B: employee2
Permissions: User A has NO permissions on User B
Request: PUT /users/{employee2_id}
Body: {"email": "new@example.com"}

Flow:
1. is_self_update = False
2. Check ACL: employee1 has NO 'write' on employee2 ✗
3. Raise HTTPException(403, "You don't have permission to modify this user")
4. Return 403 Forbidden
```

## Field-Level ACL Integration

When ACL returns field restrictions:

```
User A: manager
User B: employee
Permission: User A has 'write' on User B with fields=['email', 'first_name']

Request: PUT /users/{employee_id}
Body: {"email": "new@example.com", "last_name": "Smith"}

Flow:
1. is_self_update = False
2. Check ACL: manager has 'write' on employee ✓
3. ACL returns fields=['email', 'first_name']
4. Check each update field:
   - 'email' in ['email', 'first_name'] ✓
   - 'last_name' NOT in ['email', 'first_name'] ✗
5. Raise HTTPException(403, "You don't have permission to modify field 'last_name'")
6. Return 403 Forbidden
```

## Decision Matrix

| Actor    | Target       | Field Type | ACL Perm | Result  | Reason                          |
|----------|--------------|------------|----------|---------|----------------------------------|
| User     | Self         | Allowed    | N/A      | ✓ Allow | Business rule permits           |
| User     | Self         | Forbidden  | N/A      | ✗ Deny  | Business rule blocks            |
| Admin    | Self         | Any        | N/A      | ✓ Allow | Admin bypass                    |
| User     | Other        | Any        | None     | ✗ Deny  | No ACL permission               |
| User     | Other        | Any        | Write    | ✓ Allow | ACL permits                     |
| User     | Other        | Any        | Write*   | Partial | ACL field restrictions apply    |
| Admin    | Other        | Any        | N/A      | ✓ Allow | Admin bypass                    |

*Write with field restrictions: only specific fields can be modified

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     User Update Endpoint                     │
│                    (app/api/users.py)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │                         │
        ▼                         ▼
┌───────────────────┐    ┌─────────────────────┐
│  Business Rules   │    │   ACL Permission    │
│  (business_rules) │    │   (permission_svc)  │
└───────────────────┘    └─────────────────────┘
        │                         │
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │  Database Update │
           │   (SQLAlchemy)   │
           └──────────────────┘
```

## Key Design Principles

1. **Separation of Concerns**
   - Business rules in `business_rules.py`
   - ACL checks in `permission_service.py`
   - Both are independent but complementary

2. **Admin Privilege**
   - `is_admin=True` bypasses self-update rules
   - Admins can modify any field on any user (including self)

3. **Self-Update Focus**
   - Self-update rules ONLY apply when user_id == current_user.id
   - Cross-user updates use ACL exclusively

4. **Field-Level Control**
   - ACL can specify allowed fields
   - Self-update rules specify forbidden fields (for self-updates)
   - Both can restrict fields, but at different layers

5. **Fail-Secure**
   - Default deny if no explicit permission
   - Multiple validation layers (business + ACL)
   - Clear error messages for debugging
