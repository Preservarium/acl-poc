"""Create admin user for testing."""

import asyncio
from app.database import AsyncSessionLocal, engine
from app.models import Base, User
from app.core.security import get_password_hash


async def create_admin():
    """Create admin and test users."""
    print("Creating database tables...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Creating users...")

    # Create test users
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
        )
        db.add(admin)

        # Create regular users
        alice = User(
            username="alice",
            password_hash=get_password_hash("alice123"),
            is_admin=False,
        )
        db.add(alice)

        bob = User(
            username="bob",
            password_hash=get_password_hash("bob123"),
            is_admin=False,
        )
        db.add(bob)

        await db.commit()

    print("\nUsers created successfully!")
    print("------------------------")
    print("Admin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nRegular users:")
    print("  Username: alice, Password: alice123")
    print("  Username: bob, Password: bob123")


if __name__ == "__main__":
    asyncio.run(create_admin())
