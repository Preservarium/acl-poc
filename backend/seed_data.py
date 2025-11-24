#!/usr/bin/env python3
"""
Seed data script for ACL PoC.

Creates initial data matching the test scenarios:
- Users: admin, alice, bob, carol
- Groups: ops-team, viewers
- Sites: Factory-1, Factory-2
- Plans: Floor-A, Floor-B
- Sensors: Temp-1, Humidity-1
- Permissions: as specified in test scenarios

This script is idempotent - it can be run multiple times safely.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import User, Group, Site, Plan, Sensor, ResourcePermission
from app.models.permission import GranteeType, ResourceType, Permission, Effect
from app.core.security import get_password_hash
from app.config import settings


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """Create initial users."""
    print("\nSeeding users...")

    users = {}
    user_data = [
        {"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD, "is_admin": True},
        {"username": "alice", "password": "alice123", "is_admin": False},
        {"username": "bob", "password": "bob123", "is_admin": False},
        {"username": "carol", "password": "carol123", "is_admin": False},
    ]

    for data in user_data:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.username == data["username"])
        )
        user = result.scalar_one_or_none()

        if user:
            print(f"  User '{data['username']}' already exists")
            users[data["username"]] = user
        else:
            user = User(
                username=data["username"],
                password_hash=get_password_hash(data["password"]),
                is_admin=data["is_admin"]
            )
            session.add(user)
            await session.flush()
            print(f"  Created user '{data['username']}' (admin={data['is_admin']})")
            users[data["username"]] = user

    await session.commit()
    return users


async def seed_groups(session: AsyncSession, users: dict[str, User]) -> dict[str, Group]:
    """Create initial groups and assign members."""
    print("\nSeeding groups...")

    groups = {}
    group_data = [
        {"name": "ops-team", "members": ["bob", "carol"]},
        {"name": "viewers", "members": ["carol"]},
    ]

    for data in group_data:
        # Check if group already exists
        result = await session.execute(
            select(Group).where(Group.name == data["name"])
        )
        group = result.scalar_one_or_none()

        if group:
            print(f"  Group '{data['name']}' already exists")
            groups[data["name"]] = group
        else:
            group = Group(name=data["name"])

            # Add members
            for username in data["members"]:
                if username in users:
                    group.users.append(users[username])

            session.add(group)
            await session.flush()
            print(f"  Created group '{data['name']}' with members: {', '.join(data['members'])}")
            groups[data["name"]] = group

    await session.commit()
    return groups


async def seed_sites(session: AsyncSession, users: dict[str, User]) -> dict[str, Site]:
    """Create initial sites."""
    print("\nSeeding sites...")

    sites = {}
    site_data = [
        {"name": "Factory-1", "created_by": "admin"},
        {"name": "Factory-2", "created_by": "admin"},
    ]

    admin = users.get("admin")

    for data in site_data:
        # Check if site already exists
        result = await session.execute(
            select(Site).where(Site.name == data["name"])
        )
        site = result.scalar_one_or_none()

        if site:
            print(f"  Site '{data['name']}' already exists")
            sites[data["name"]] = site
        else:
            site = Site(
                name=data["name"],
                created_by=admin.id if admin else None
            )
            session.add(site)
            await session.flush()
            print(f"  Created site '{data['name']}'")
            sites[data["name"]] = site

    await session.commit()
    return sites


async def seed_plans(
    session: AsyncSession,
    sites: dict[str, Site],
    users: dict[str, User]
) -> dict[str, Plan]:
    """Create initial plans."""
    print("\nSeeding plans...")

    plans = {}
    plan_data = [
        {"name": "Floor-A", "site": "Factory-1", "created_by": "admin"},
        {"name": "Floor-B", "site": "Factory-1", "created_by": "admin"},
    ]

    admin = users.get("admin")

    for data in plan_data:
        # Check if plan already exists
        site = sites.get(data["site"])
        if not site:
            print(f"  Warning: Site '{data['site']}' not found for plan '{data['name']}'")
            continue

        result = await session.execute(
            select(Plan).where(Plan.name == data["name"], Plan.site_id == site.id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            print(f"  Plan '{data['name']}' already exists")
            plans[data["name"]] = plan
        else:
            plan = Plan(
                name=data["name"],
                site_id=site.id,
                created_by=admin.id if admin else None
            )
            session.add(plan)
            await session.flush()
            print(f"  Created plan '{data['name']}' in site '{data['site']}'")
            plans[data["name"]] = plan

    await session.commit()
    return plans


async def seed_sensors(
    session: AsyncSession,
    plans: dict[str, Plan],
    users: dict[str, User]
) -> dict[str, Sensor]:
    """Create initial sensors."""
    print("\nSeeding sensors...")

    sensors = {}
    sensor_data = [
        {"name": "Temp-1", "plan": "Floor-A", "created_by": "admin"},
        {"name": "Humidity-1", "plan": "Floor-A", "created_by": "admin"},
    ]

    admin = users.get("admin")

    for data in sensor_data:
        # Check if sensor already exists
        plan = plans.get(data["plan"])
        if not plan:
            print(f"  Warning: Plan '{data['plan']}' not found for sensor '{data['name']}'")
            continue

        result = await session.execute(
            select(Sensor).where(Sensor.name == data["name"], Sensor.plan_id == plan.id)
        )
        sensor = result.scalar_one_or_none()

        if sensor:
            print(f"  Sensor '{data['name']}' already exists")
            sensors[data["name"]] = sensor
        else:
            sensor = Sensor(
                name=data["name"],
                plan_id=plan.id,
                created_by=admin.id if admin else None
            )
            session.add(sensor)
            await session.flush()
            print(f"  Created sensor '{data['name']}' in plan '{data['plan']}'")
            sensors[data["name"]] = sensor

    await session.commit()
    return sensors


async def seed_permissions(
    session: AsyncSession,
    users: dict[str, User],
    groups: dict[str, Group],
    sites: dict[str, Site],
    plans: dict[str, Plan]
):
    """Create initial permissions."""
    print("\nSeeding permissions...")

    permission_data = [
        # Admin manage permissions on both sites
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "admin",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory-1",
            "permission": Permission.MANAGE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "description": "admin → Factory-1 → manage (inherit=true)"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "admin",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory-2",
            "permission": Permission.MANAGE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "description": "admin → Factory-2 → manage (inherit=true)"
        },
        # Alice read permission on Factory-1
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "alice",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory-1",
            "permission": Permission.READ,
            "effect": Effect.ALLOW,
            "inherit": True,
            "description": "alice → Factory-1 → read (inherit=true)"
        },
        # ops-team write permission on Floor-A
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "ops-team",
            "resource_type": ResourceType.PLAN,
            "resource_id": "Floor-A",
            "permission": Permission.WRITE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "description": "ops-team → Floor-A → write (inherit=true)"
        },
    ]

    for data in permission_data:
        # Resolve grantee ID
        if data["grantee_type"] == GranteeType.USER:
            grantee = users.get(data["grantee_id"])
            if not grantee:
                print(f"  Warning: User '{data['grantee_id']}' not found")
                continue
            grantee_id = grantee.id
        else:  # GROUP
            grantee = groups.get(data["grantee_id"])
            if not grantee:
                print(f"  Warning: Group '{data['grantee_id']}' not found")
                continue
            grantee_id = grantee.id

        # Resolve resource ID
        if data["resource_type"] == ResourceType.SITE:
            resource = sites.get(data["resource_id"])
        elif data["resource_type"] == ResourceType.PLAN:
            resource = plans.get(data["resource_id"])
        else:
            print(f"  Warning: Unsupported resource type '{data['resource_type']}'")
            continue

        if not resource:
            print(f"  Warning: Resource '{data['resource_id']}' not found")
            continue

        resource_id = resource.id

        # Check if permission already exists
        result = await session.execute(
            select(ResourcePermission).where(
                ResourcePermission.grantee_type == data["grantee_type"],
                ResourcePermission.grantee_id == grantee_id,
                ResourcePermission.resource_type == data["resource_type"],
                ResourcePermission.resource_id == resource_id,
                ResourcePermission.permission == data["permission"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Permission already exists: {data['description']}")
        else:
            permission = ResourcePermission(
                grantee_type=data["grantee_type"],
                grantee_id=grantee_id,
                resource_type=data["resource_type"],
                resource_id=resource_id,
                permission=data["permission"],
                effect=data["effect"],
                inherit=data["inherit"],
                granted_by=None  # System-granted
            )
            session.add(permission)
            print(f"  Created permission: {data['description']}")

    await session.commit()


async def main():
    """Main seed data function."""
    print("=" * 60)
    print("ACL PoC - Seed Data Script")
    print("=" * 60)

    try:
        # Create tables
        await create_tables()

        # Get database session
        async with AsyncSessionLocal() as session:
            # Seed in order (respecting dependencies)
            users = await seed_users(session)
            groups = await seed_groups(session, users)
            sites = await seed_sites(session, users)
            plans = await seed_plans(session, sites, users)
            sensors = await seed_sensors(session, plans, users)
            await seed_permissions(session, users, groups, sites, plans)

        print("\n" + "=" * 60)
        print("Seed data created successfully!")
        print("=" * 60)
        print("\nDefault credentials:")
        print(f"  Username: {settings.ADMIN_USERNAME}")
        print(f"  Password: {settings.ADMIN_PASSWORD}")
        print("\nOther test users:")
        print("  alice / alice123")
        print("  bob / bob123")
        print("  carol / carol123")
        print("\n")

    except Exception as e:
        print(f"\nError seeding data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
