"""Simple test script to verify permission hierarchy without pytest."""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.user import User
from app.models.site import Site
from app.models.permission import (
    ResourcePermission,
    GranteeType,
    ResourceType,
    Permission,
    Effect,
)
from app.services.permission_service import PermissionService, PERMISSION_HIERARCHY, expand_permission
from app.core.security import get_password_hash


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def test_permission_hierarchy():
    """Test permission hierarchy implementation."""

    print("\n" + "="*60)
    print("PERMISSION HIERARCHY TESTS")
    print("="*60)

    # Test 1: Check PERMISSION_HIERARCHY constant
    print("\n[Test 1] Checking PERMISSION_HIERARCHY constant...")

    expected_read = [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE, Permission.MANAGE]
    actual_read = PERMISSION_HIERARCHY[Permission.READ]
    assert actual_read == expected_read, f"Expected {expected_read}, got {actual_read}"
    print("  ✓ READ implies: READ, WRITE, DELETE, CREATE, MANAGE")

    expected_write = [Permission.WRITE, Permission.MANAGE]
    actual_write = PERMISSION_HIERARCHY[Permission.WRITE]
    assert actual_write == expected_write, f"Expected {expected_write}, got {actual_write}"
    print("  ✓ WRITE implies: WRITE, MANAGE")

    expected_manage = [Permission.MANAGE]
    actual_manage = PERMISSION_HIERARCHY[Permission.MANAGE]
    assert actual_manage == expected_manage, f"Expected {expected_manage}, got {actual_manage}"
    print("  ✓ MANAGE implies: MANAGE")

    # Test 2: Check expand_permission function
    print("\n[Test 2] Checking expand_permission function...")

    expanded_read = expand_permission(Permission.READ)
    assert expanded_read == expected_read, f"Expected {expected_read}, got {expanded_read}"
    print(f"  ✓ expand_permission(READ) = {[p.value for p in expanded_read]}")

    expanded_manage = expand_permission(Permission.MANAGE)
    assert expanded_manage == expected_manage, f"Expected {expected_manage}, got {expanded_manage}"
    print(f"  ✓ expand_permission(MANAGE) = {[p.value for p in expanded_manage]}")

    # Test 3: Integration test with database
    print("\n[Test 3] Integration test with database...")

    # Create database
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create test user
        user = User(
            username="testuser",
            password_hash=get_password_hash("password"),
            is_admin=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"  ✓ Created test user: {user.username}")

        # Create test site
        site = Site(name="Test Site", created_by=user.id)
        db.add(site)
        await db.commit()
        await db.refresh(site)
        print(f"  ✓ Created test site: {site.name}")

        # Create permission service
        perm_service = PermissionService(db)

        # Test 3a: Grant MANAGE permission
        print("\n[Test 3a] Testing MANAGE grants READ access...")
        await perm_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=user.id,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.MANAGE,
        )
        print("  ✓ Granted MANAGE permission to user on site")

        # Check READ permission (should pass because MANAGE implies READ)
        allowed, fields = await perm_service.check(
            user=user,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.READ,
        )
        assert allowed is True, "MANAGE should grant READ access"
        assert fields is None, "Fields should be None (all fields)"
        print("  ✓ User with MANAGE can READ (hierarchy working)")

        # Check WRITE permission (should pass because MANAGE implies WRITE)
        allowed, fields = await perm_service.check(
            user=user,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.WRITE,
        )
        assert allowed is True, "MANAGE should grant WRITE access"
        print("  ✓ User with MANAGE can WRITE (hierarchy working)")

        # Clean up for next test
        await db.execute(
            "DELETE FROM resource_permissions WHERE grantee_id = :user_id",
            {"user_id": user.id}
        )
        await db.commit()

        # Test 3b: Grant WRITE permission
        print("\n[Test 3b] Testing WRITE grants READ access...")
        await perm_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=user.id,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.WRITE,
        )
        print("  ✓ Granted WRITE permission to user on site")

        # Check READ permission (should pass because WRITE implies READ)
        allowed, fields = await perm_service.check(
            user=user,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.READ,
        )
        assert allowed is True, "WRITE should grant READ access"
        print("  ✓ User with WRITE can READ (hierarchy working)")

        # Check MANAGE permission (should fail because WRITE does NOT imply MANAGE)
        allowed, fields = await perm_service.check(
            user=user,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.MANAGE,
        )
        assert allowed is False, "WRITE should NOT grant MANAGE access"
        print("  ✓ User with WRITE cannot MANAGE (hierarchy working correctly)")

        # Clean up for next test
        await db.execute(
            "DELETE FROM resource_permissions WHERE grantee_id = :user_id",
            {"user_id": user.id}
        )
        await db.commit()

        # Test 3c: Grant READ permission
        print("\n[Test 3c] Testing READ does NOT grant WRITE access...")
        await perm_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=user.id,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.READ,
        )
        print("  ✓ Granted READ permission to user on site")

        # Check WRITE permission (should fail because READ does NOT imply WRITE)
        allowed, fields = await perm_service.check(
            user=user,
            resource_type=ResourceType.SITE,
            resource_id=site.id,
            permission=Permission.WRITE,
        )
        assert allowed is False, "READ should NOT grant WRITE access"
        print("  ✓ User with READ cannot WRITE (hierarchy working correctly)")

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")

    return True


async def main():
    """Run all tests."""
    try:
        await test_permission_hierarchy()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
