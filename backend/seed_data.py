#!/usr/bin/env python3
"""
Seed data script for ACL PoC v3.

Creates initial data matching the v3 spec test scenarios:
- Users (6): admin, alice, bob, carol, dave, eve
- Groups (4 standalone): Factory 1 Admins, Factory 1 Operators, Factory 1 Viewers, Global Operators
- Sites (2): Factory 1, Factory 2
- Plans (3): Floor A, Floor B (Factory 1), Floor C (Factory 2)
- Sensors (3): Temp Sensor #1, Humidity Sensor #1 (Floor A), Pressure Sensor #1 (Floor B)
- Brokers (2): MQTT Broker #1, CoAP Gateway (Floor A)
- Alarms (2): High Temperature, Low Humidity
- Alerts (1): Temperature exceeded 30°C
- Dashboards (1): Main Dashboard
- Permissions: Group memberships, group permissions, direct user permissions

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
    """Create initial users (6 total)."""
    print("\nSeeding users...")

    users = {}
    user_data = [
        {"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD, "is_admin": True},
        {"username": "alice", "password": "alice123", "is_admin": False},
        {"username": "bob", "password": "bob123", "is_admin": False},
        {"username": "carol", "password": "carol123", "is_admin": False},
        {"username": "dave", "password": "dave123", "is_admin": False},
        {"username": "eve", "password": "eve123", "is_admin": False},
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
    """Create initial groups (standalone, no site_id)."""
    print("\nSeeding groups...")

    groups = {}
    group_data = [
        {"name": "Factory 1 Admins", "description": "Administrators for Factory 1"},
        {"name": "Factory 1 Operators", "description": "Operators for Factory 1"},
        {"name": "Factory 1 Viewers", "description": "Read-only access to Factory 1"},
        {"name": "Global Operators", "description": "Operators across all sites"},
    ]

    admin = users.get("admin")

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
            group = Group(
                name=data["name"],
                description=data.get("description"),
                created_by=admin.id if admin else None
            )
            session.add(group)
            await session.flush()
            print(f"  Created group '{data['name']}'")
            groups[data["name"]] = group

    await session.commit()
    return groups


async def seed_sites(session: AsyncSession, users: dict[str, User]) -> dict[str, Site]:
    """Create initial sites (2 total)."""
    print("\nSeeding sites...")

    sites = {}
    site_data = [
        {"name": "Factory 1", "description": "Primary manufacturing facility"},
        {"name": "Factory 2", "description": "Secondary manufacturing facility"},
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
                description=data.get("description"),
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
    """Create initial plans (3 total)."""
    print("\nSeeding plans...")

    plans = {}
    plan_data = [
        {"name": "Floor A", "site": "Factory 1", "description": "Production floor - main assembly"},
        {"name": "Floor B", "site": "Factory 1", "description": "Warehouse and storage"},
        {"name": "Floor C", "site": "Factory 2", "description": "Research and development"},
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
                description=data.get("description"),
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
    """Create initial sensors (3 total with field_a-e)."""
    print("\nSeeding sensors...")

    sensors = {}
    sensor_data = [
        {
            "name": "Temp Sensor #1",
            "plan": "Floor A",
            "field_a": "23.5",
            "field_b": "65",
            "field_c": "1013",
            "field_d": "2024-01-15",
            "field_e": '{"interval":60}'
        },
        {
            "name": "Humidity Sensor #1",
            "plan": "Floor A",
            "field_a": "65",
            "field_b": "23",
            "field_c": "1015",
            "field_d": "2024-01-20",
            "field_e": '{"interval":120}'
        },
        {
            "name": "Pressure Sensor #1",
            "plan": "Floor B",
            "field_a": "1013",
            "field_b": "24",
            "field_c": "66",
            "field_d": "2024-02-01",
            "field_e": '{"interval":60}'
        },
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
            # Create sensor with available fields
            sensor_kwargs = {
                "name": data["name"],
                "plan_id": plan.id,
                "created_by": admin.id if admin else None
            }

            # Add field_a-e if they exist in the model
            for field in ["field_a", "field_b", "field_c", "field_d", "field_e"]:
                if hasattr(Sensor, field) and field in data:
                    sensor_kwargs[field] = data[field]

            sensor = Sensor(**sensor_kwargs)
            session.add(sensor)
            await session.flush()
            print(f"  Created sensor '{data['name']}' in plan '{data['plan']}'")
            sensors[data["name"]] = sensor

    await session.commit()
    return sensors


async def seed_brokers(
    session: AsyncSession,
    plans: dict[str, Plan],
    users: dict[str, User]
) -> dict[str, any]:
    """Create initial brokers (if Broker model exists)."""
    print("\nSeeding brokers...")

    brokers = {}

    # Check if Broker model exists
    try:
        from app.models import Broker
    except (ImportError, AttributeError):
        print("  Broker model not found - skipping broker creation")
        return brokers

    broker_data = [
        {
            "name": "MQTT Broker #1",
            "protocol": "mqtt",
            "host": "192.168.1.100",
            "port": 1883,
            "plan": "Floor A"
        },
        {
            "name": "CoAP Gateway",
            "protocol": "coap",
            "host": "192.168.1.101",
            "port": 5683,
            "plan": "Floor A"
        },
    ]

    admin = users.get("admin")

    for data in broker_data:
        plan = plans.get(data["plan"])
        if not plan:
            print(f"  Warning: Plan '{data['plan']}' not found for broker '{data['name']}'")
            continue

        result = await session.execute(
            select(Broker).where(Broker.name == data["name"], Broker.plan_id == plan.id)
        )
        broker = result.scalar_one_or_none()

        if broker:
            print(f"  Broker '{data['name']}' already exists")
            brokers[data["name"]] = broker
        else:
            broker = Broker(
                name=data["name"],
                protocol=data["protocol"],
                host=data["host"],
                port=data["port"],
                plan_id=plan.id,
                created_by=admin.id if admin else None
            )
            session.add(broker)
            await session.flush()
            print(f"  Created broker '{data['name']}' in plan '{data['plan']}'")
            brokers[data["name"]] = broker

    await session.commit()
    return brokers


async def seed_alarms(
    session: AsyncSession,
    sensors: dict[str, any],
    users: dict[str, User]
) -> dict[str, any]:
    """Create initial alarms (if Alarm model exists)."""
    print("\nSeeding alarms...")

    alarms = {}

    # Check if Alarm model exists
    try:
        from app.models import Alarm
    except (ImportError, AttributeError):
        print("  Alarm model not found - skipping alarm creation")
        return alarms

    alarm_data = [
        {
            "name": "High Temperature",
            "threshold": 30.0,
            "condition": "gt",
            "active": True,
            "sensor": "Temp Sensor #1"
        },
        {
            "name": "Low Humidity",
            "threshold": 40.0,
            "condition": "lt",
            "active": True,
            "sensor": "Humidity Sensor #1"
        },
    ]

    admin = users.get("admin")

    for data in alarm_data:
        sensor = sensors.get(data["sensor"])
        if not sensor:
            print(f"  Warning: Sensor '{data['sensor']}' not found for alarm '{data['name']}'")
            continue

        result = await session.execute(
            select(Alarm).where(Alarm.name == data["name"], Alarm.sensor_id == sensor.id)
        )
        alarm = result.scalar_one_or_none()

        if alarm:
            print(f"  Alarm '{data['name']}' already exists")
            alarms[data["name"]] = alarm
        else:
            alarm = Alarm(
                name=data["name"],
                threshold=data["threshold"],
                condition=data["condition"],
                active=data["active"],
                sensor_id=sensor.id,
                created_by=admin.id if admin else None
            )
            session.add(alarm)
            await session.flush()
            print(f"  Created alarm '{data['name']}' on sensor '{data['sensor']}'")
            alarms[data["name"]] = alarm

    await session.commit()
    return alarms


async def seed_alerts(
    session: AsyncSession,
    alarms: dict[str, any]
) -> dict[str, any]:
    """Create initial alerts (if Alert model exists)."""
    print("\nSeeding alerts...")

    alerts = {}

    # Check if Alert model exists
    try:
        from app.models import Alert
        from datetime import datetime
    except (ImportError, AttributeError):
        print("  Alert model not found - skipping alert creation")
        return alerts

    alert_data = [
        {
            "message": "Temperature exceeded 30°C",
            "severity": "warning",
            "triggered_at": "2024-11-25 10:00:00",
            "acknowledged": False,
            "alarm": "High Temperature"
        },
    ]

    for data in alert_data:
        alarm = alarms.get(data["alarm"])
        if not alarm:
            print(f"  Warning: Alarm '{data['alarm']}' not found for alert")
            continue

        result = await session.execute(
            select(Alert).where(
                Alert.message == data["message"],
                Alert.alarm_id == alarm.id
            )
        )
        alert = result.scalar_one_or_none()

        if alert:
            print(f"  Alert '{data['message']}' already exists")
            alerts[data["message"]] = alert
        else:
            alert = Alert(
                message=data["message"],
                severity=data["severity"],
                triggered_at=datetime.fromisoformat(data["triggered_at"]),
                acknowledged=data["acknowledged"],
                alarm_id=alarm.id
            )
            session.add(alert)
            await session.flush()
            print(f"  Created alert '{data['message']}'")
            alerts[data["message"]] = alert

    await session.commit()
    return alerts


async def seed_dashboards(
    session: AsyncSession,
    users: dict[str, User]
) -> dict[str, any]:
    """Create initial dashboards (if Dashboard model exists)."""
    print("\nSeeding dashboards...")

    dashboards = {}

    # Check if Dashboard model exists
    try:
        from app.models import Dashboard
    except (ImportError, AttributeError):
        print("  Dashboard model not found - skipping dashboard creation")
        return dashboards

    dashboard_data = [
        {
            "name": "Main Dashboard",
            "config": '{"widgets":[]}',
            "created_by": "alice"
        },
    ]

    for data in dashboard_data:
        creator = users.get(data["created_by"])
        if not creator:
            print(f"  Warning: User '{data['created_by']}' not found for dashboard '{data['name']}'")
            continue

        result = await session.execute(
            select(Dashboard).where(Dashboard.name == data["name"])
        )
        dashboard = result.scalar_one_or_none()

        if dashboard:
            print(f"  Dashboard '{data['name']}' already exists")
            dashboards[data["name"]] = dashboard
        else:
            dashboard = Dashboard(
                name=data["name"],
                config=data["config"],
                created_by=creator.id
            )
            session.add(dashboard)
            await session.flush()
            print(f"  Created dashboard '{data['name']}' by {data['created_by']}")
            dashboards[data["name"]] = dashboard

    await session.commit()
    return dashboards


async def seed_permissions(
    session: AsyncSession,
    users: dict[str, User],
    groups: dict[str, Group],
    sites: dict[str, Site],
    plans: dict[str, Plan],
    dashboards: dict[str, any] = None
):
    """Create initial permissions matching v3 spec."""
    print("\nSeeding permissions...")

    if dashboards is None:
        dashboards = {}

    permission_data = [
        # GROUP MEMBERSHIPS (using 'member' permission)
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "alice",
            "resource_type": "group",
            "resource_id": "Factory 1 Admins",
            "permission": "member",
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "alice → Factory 1 Admins → member"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "bob",
            "resource_type": "group",
            "resource_id": "Factory 1 Operators",
            "permission": "member",
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "bob → Factory 1 Operators → member"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "carol",
            "resource_type": "group",
            "resource_id": "Factory 1 Viewers",
            "permission": "member",
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "carol → Factory 1 Viewers → member"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "dave",
            "resource_type": "group",
            "resource_id": "Factory 1 Operators",
            "permission": "member",
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "dave → Factory 1 Operators → member"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "dave",
            "resource_type": "group",
            "resource_id": "Global Operators",
            "permission": "member",
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "dave → Global Operators → member"
        },

        # GROUP PERMISSIONS ON RESOURCES
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "Factory 1 Admins",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory 1",
            "permission": Permission.MANAGE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "fields": None,
            "description": "Factory 1 Admins → site:Factory 1 → manage (inherit=true)"
        },
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "Factory 1 Operators",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory 1",
            "permission": Permission.WRITE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "fields": ["field_a", "field_b", "field_c"],
            "description": "Factory 1 Operators → site:Factory 1 → write (inherit=true, fields=a,b,c)"
        },
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "Factory 1 Viewers",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory 1",
            "permission": Permission.READ,
            "effect": Effect.ALLOW,
            "inherit": True,
            "fields": None,
            "description": "Factory 1 Viewers → site:Factory 1 → read (inherit=true)"
        },
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "Global Operators",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory 1",
            "permission": Permission.WRITE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "fields": None,
            "description": "Global Operators → site:Factory 1 → write (inherit=true)"
        },
        {
            "grantee_type": GranteeType.GROUP,
            "grantee_id": "Global Operators",
            "resource_type": ResourceType.SITE,
            "resource_id": "Factory 2",
            "permission": Permission.WRITE,
            "effect": Effect.ALLOW,
            "inherit": True,
            "fields": None,
            "description": "Global Operators → site:Factory 2 → write (inherit=true)"
        },

        # DIRECT USER PERMISSIONS
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "dave",
            "resource_type": ResourceType.PLAN,
            "resource_id": "Floor A",
            "permission": Permission.WRITE,
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": ["field_d", "field_e"],
            "description": "dave → plan:Floor A → write (inherit=false, fields=d,e)"
        },
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "bob",
            "resource_type": ResourceType.PLAN,
            "resource_id": "Floor B",
            "permission": Permission.READ,
            "effect": Effect.DENY,
            "inherit": True,
            "fields": None,
            "description": "bob → plan:Floor B → read (effect=deny, inherit=true)"
        },

        # DASHBOARD PERMISSION (if dashboards exist)
        {
            "grantee_type": GranteeType.USER,
            "grantee_id": "alice",
            "resource_type": "dashboard",
            "resource_id": "Main Dashboard",
            "permission": Permission.MANAGE,
            "effect": Effect.ALLOW,
            "inherit": False,
            "fields": None,
            "description": "alice → dashboard:Main Dashboard → manage (inherit=false)"
        },
    ]

    import json

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

        # Resolve resource ID based on resource_type
        resource_type_str = str(data["resource_type"]).split(".")[-1].lower() if hasattr(data["resource_type"], "value") else data["resource_type"]

        if resource_type_str == "site":
            resource = sites.get(data["resource_id"])
        elif resource_type_str == "plan":
            resource = plans.get(data["resource_id"])
        elif resource_type_str == "group":
            resource = groups.get(data["resource_id"])
        elif resource_type_str == "dashboard":
            resource = dashboards.get(data["resource_id"])
        else:
            print(f"  Warning: Unsupported resource type '{resource_type_str}'")
            continue

        if not resource:
            # Skip dashboard permissions if dashboard doesn't exist
            if resource_type_str == "dashboard":
                print(f"  Skipping permission for non-existent dashboard '{data['resource_id']}'")
                continue
            print(f"  Warning: Resource '{data['resource_id']}' not found")
            continue

        resource_id = resource.id

        # Prepare permission value
        perm_value = data["permission"]
        if hasattr(perm_value, "value"):
            perm_value = perm_value.value
        elif isinstance(perm_value, str):
            perm_value = perm_value

        # Check if permission already exists
        result = await session.execute(
            select(ResourcePermission).where(
                ResourcePermission.grantee_type == data["grantee_type"],
                ResourcePermission.grantee_id == grantee_id,
                ResourcePermission.resource_type == resource_type_str,
                ResourcePermission.resource_id == resource_id,
                ResourcePermission.permission == perm_value
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Permission already exists: {data['description']}")
        else:
            # Prepare fields as JSON if they exist
            fields_json = None
            if data.get("fields") is not None:
                fields_json = json.dumps(data["fields"])

            permission_kwargs = {
                "grantee_type": data["grantee_type"],
                "grantee_id": grantee_id,
                "resource_type": resource_type_str,
                "resource_id": resource_id,
                "permission": perm_value,
                "effect": data["effect"],
                "inherit": data["inherit"],
                "granted_by": None  # System-granted
            }

            # Add fields if the model supports it
            if hasattr(ResourcePermission, "fields"):
                permission_kwargs["fields"] = fields_json

            permission = ResourcePermission(**permission_kwargs)
            session.add(permission)
            print(f"  Created permission: {data['description']}")

    await session.commit()


async def main():
    """Main seed data function."""
    print("=" * 60)
    print("ACL PoC v3 - Seed Data Script")
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
            brokers = await seed_brokers(session, plans, users)
            alarms = await seed_alarms(session, sensors, users)
            alerts = await seed_alerts(session, alarms)
            dashboards = await seed_dashboards(session, users)
            await seed_permissions(session, users, groups, sites, plans, dashboards)

        print("\n" + "=" * 60)
        print("Seed data created successfully!")
        print("=" * 60)
        print("\nDefault credentials:")
        print(f"  Username: {settings.ADMIN_USERNAME}")
        print(f"  Password: {settings.ADMIN_PASSWORD}")
        print("\nTest users:")
        print("  alice / alice123  (Factory 1 Admins)")
        print("  bob / bob123      (Factory 1 Operators)")
        print("  carol / carol123  (Factory 1 Viewers)")
        print("  dave / dave123    (Factory 1 Operators + Global Operators)")
        print("  eve / eve123      (no permissions)")
        print("\nGroups:")
        print("  - Factory 1 Admins")
        print("  - Factory 1 Operators")
        print("  - Factory 1 Viewers")
        print("  - Global Operators")
        print("\nResources:")
        print("  Sites: Factory 1, Factory 2")
        print("  Plans: Floor A, Floor B (Factory 1), Floor C (Factory 2)")
        print("  Sensors: 3 (with field_a-e if supported)")
        print("  Brokers: 2 (if supported)")
        print("  Alarms: 2 (if supported)")
        print("  Alerts: 1 (if supported)")
        print("  Dashboards: 1 (if supported)")
        print("\n")

    except Exception as e:
        print(f"\nError seeding data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
