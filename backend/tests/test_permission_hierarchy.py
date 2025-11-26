"""Unit tests for permission hierarchy implication."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.models import Base
from app.models.user import User
from app.models.site import Site
from app.models.plan import Plan
from app.models.sensor import Sensor
from app.models.permission import (
    ResourcePermission,
    GranteeType,
    ResourceType,
    Permission,
    Effect,
)
from app.services.permission_service import PermissionService, PERMISSION_HIERARCHY
from app.core.security import get_password_hash


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash=get_password_hash("password"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_site(db_session: AsyncSession, test_user: User):
    """Create a test site."""
    site = Site(
        name="Test Site",
        created_by=test_user.id,
    )
    db_session.add(site)
    await db_session.commit()
    await db_session.refresh(site)
    return site


@pytest.fixture
async def test_plan(db_session: AsyncSession, test_user: User, test_site: Site):
    """Create a test plan."""
    plan = Plan(
        name="Test Plan",
        site_id=test_site.id,
        created_by=test_user.id,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.fixture
async def test_sensor(db_session: AsyncSession, test_user: User, test_plan: Plan):
    """Create a test sensor."""
    sensor = Sensor(
        name="Test Sensor",
        plan_id=test_plan.id,
        created_by=test_user.id,
    )
    db_session.add(sensor)
    await db_session.commit()
    await db_session.refresh(sensor)
    return sensor


@pytest.fixture
def permission_service(db_session: AsyncSession):
    """Create a permission service instance."""
    return PermissionService(db_session)


class TestPermissionHierarchyConstants:
    """Test the PERMISSION_HIERARCHY constant."""

    def test_read_implies_all_permissions(self):
        """Test that read is implied by all higher permissions."""
        expected = [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE, Permission.MANAGE]
        assert PERMISSION_HIERARCHY[Permission.READ] == expected

    def test_write_implies_write_and_manage(self):
        """Test that write is implied by write and manage."""
        expected = [Permission.WRITE, Permission.MANAGE]
        assert PERMISSION_HIERARCHY[Permission.WRITE] == expected

    def test_delete_implies_delete_and_manage(self):
        """Test that delete is implied by delete and manage."""
        expected = [Permission.DELETE, Permission.MANAGE]
        assert PERMISSION_HIERARCHY[Permission.DELETE] == expected

    def test_create_implies_create_and_manage(self):
        """Test that create is implied by create and manage."""
        expected = [Permission.CREATE, Permission.MANAGE]
        assert PERMISSION_HIERARCHY[Permission.CREATE] == expected

    def test_manage_implies_only_manage(self):
        """Test that manage is only implied by manage."""
        expected = [Permission.MANAGE]
        assert PERMISSION_HIERARCHY[Permission.MANAGE] == expected


class TestPermissionImplication:
    """Test permission implication in permission checks."""

    @pytest.mark.asyncio
    async def test_manage_grants_read_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that manage permission grants read access."""
        # Grant manage permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
        )

        # Check read permission - should succeed because manage implies read
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None  # All fields

    @pytest.mark.asyncio
    async def test_manage_grants_write_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that manage permission grants write access."""
        # Grant manage permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
        )

        # Check write permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_manage_grants_delete_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that manage permission grants delete access."""
        # Grant manage permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
        )

        # Check delete permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.DELETE,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_manage_grants_create_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that manage permission grants create access."""
        # Grant manage permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
        )

        # Check create permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.CREATE,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_write_grants_read_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that write permission grants read access."""
        # Grant write permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
        )

        # Check read permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_delete_grants_read_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that delete permission grants read access."""
        # Grant delete permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.DELETE,
        )

        # Check read permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_create_grants_read_access(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that create permission grants read access."""
        # Grant create permission
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.CREATE,
        )

        # Check read permission - should succeed
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None


class TestPermissionNonImplication:
    """Test that lower permissions do NOT grant higher permissions."""

    @pytest.mark.asyncio
    async def test_read_does_not_grant_write(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that read permission does NOT grant write access."""
        # Grant read permission only
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        # Check write permission - should fail
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
        )

        assert allowed is False

    @pytest.mark.asyncio
    async def test_read_does_not_grant_delete(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that read permission does NOT grant delete access."""
        # Grant read permission only
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.READ,
        )

        # Check delete permission - should fail
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.DELETE,
        )

        assert allowed is False

    @pytest.mark.asyncio
    async def test_write_does_not_grant_manage(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that write permission does NOT grant manage access."""
        # Grant write permission only
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
        )

        # Check manage permission - should fail
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
        )

        assert allowed is False

    @pytest.mark.asyncio
    async def test_write_does_not_grant_delete(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
    ):
        """Test that write permission does NOT grant delete access."""
        # Grant write permission only
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
        )

        # Check delete permission - should fail
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.DELETE,
        )

        assert allowed is False


class TestPermissionHierarchyWithInheritance:
    """Test permission hierarchy combined with resource inheritance."""

    @pytest.mark.asyncio
    async def test_manage_on_site_grants_read_on_sensor(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
        test_sensor: Sensor,
    ):
        """Test that manage on site grants read access on child sensor."""
        # Grant manage permission on site with inheritance
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.MANAGE,
            inherit=True,
        )

        # Check read permission on sensor - should succeed
        # manage implies read, and inherits down the hierarchy
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SENSOR,
            resource_id=test_sensor.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None

    @pytest.mark.asyncio
    async def test_write_on_site_grants_read_on_plan(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_site: Site,
        test_plan: Plan,
    ):
        """Test that write on site grants read access on child plan."""
        # Grant write permission on site with inheritance
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SITE,
            resource_id=test_site.id,
            permission=Permission.WRITE,
            inherit=True,
        )

        # Check read permission on plan - should succeed
        # write implies read, and inherits down
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.PLAN,
            resource_id=test_plan.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields is None


class TestFieldLevelWithHierarchy:
    """Test field-level permissions work with permission hierarchy."""

    @pytest.mark.asyncio
    async def test_manage_with_fields_grants_read_with_same_fields(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_sensor: Sensor,
    ):
        """Test that manage with field restriction grants read with same fields."""
        # Grant manage permission with field restriction
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SENSOR,
            resource_id=test_sensor.id,
            permission=Permission.MANAGE,
            fields=["field_a", "field_b"],
        )

        # Check read permission - should succeed with same field restriction
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SENSOR,
            resource_id=test_sensor.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert set(fields) == {"field_a", "field_b"}

    @pytest.mark.asyncio
    async def test_write_with_fields_grants_read_with_same_fields(
        self,
        db_session: AsyncSession,
        permission_service: PermissionService,
        test_user: User,
        test_sensor: Sensor,
    ):
        """Test that write with field restriction grants read with same fields."""
        # Grant write permission with field restriction
        await permission_service.grant(
            grantee_type=GranteeType.USER,
            grantee_id=test_user.id,
            resource_type=ResourceType.SENSOR,
            resource_id=test_sensor.id,
            permission=Permission.WRITE,
            fields=["field_c"],
        )

        # Check read permission - should succeed with same field restriction
        allowed, fields = await permission_service.check(
            user=test_user,
            resource_type=ResourceType.SENSOR,
            resource_id=test_sensor.id,
            permission=Permission.READ,
        )

        assert allowed is True
        assert fields == ["field_c"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
