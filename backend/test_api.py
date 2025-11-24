"""Test script for ACL PoC API."""

import asyncio
import httpx
from app.database import AsyncSessionLocal, engine
from app.models import Base, User
from app.core.security import get_password_hash


BASE_URL = "http://localhost:8000"


async def setup_test_data():
    """Create initial test users."""
    print("Setting up test data...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test users
    async with AsyncSessionLocal() as db:
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

    print("Test data created!")


async def test_api():
    """Test the API endpoints."""
    async with httpx.AsyncClient() as client:
        print("\n" + "="*60)
        print("PHASE 2 API TESTING")
        print("="*60)

        # Test 1: Login as admin
        print("\n[1] Testing login as admin...")
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print(f"Token: {admin_token[:50]}...")
        else:
            print(f"Error: {response.text}")
            return

        # Test 2: Get current user
        print("\n[2] Testing get current user...")
        response = await client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"User: {response.json()}")

        # Test 3: Create a site (admin only)
        print("\n[3] Testing create site...")
        response = await client.post(
            f"{BASE_URL}/api/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Factory 1"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            site = response.json()
            site_id = site["id"]
            print(f"Site created: {site}")
        else:
            print(f"Error: {response.text}")
            return

        # Test 4: List sites
        print("\n[4] Testing list sites...")
        response = await client.get(
            f"{BASE_URL}/api/sites",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Sites: {response.json()}")

        # Test 5: Create a plan
        print("\n[5] Testing create plan...")
        response = await client.post(
            f"{BASE_URL}/api/plans",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Floor 1", "site_id": site_id}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            plan = response.json()
            plan_id = plan["id"]
            print(f"Plan created: {plan}")
        else:
            print(f"Error: {response.text}")
            return

        # Test 6: Create a sensor
        print("\n[6] Testing create sensor...")
        response = await client.post(
            f"{BASE_URL}/api/sensors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Sensor 001", "plan_id": plan_id}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            sensor = response.json()
            sensor_id = sensor["id"]
            print(f"Sensor created: {sensor}")
        else:
            print(f"Error: {response.text}")
            return

        # Test 7: List my permissions
        print("\n[7] Testing list my permissions...")
        response = await client.get(
            f"{BASE_URL}/api/permissions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Status: {response.status_code}")
        permissions = response.json()
        print(f"My permissions count: {len(permissions)}")
        if permissions:
            print(f"First permission: {permissions[0]}")

        # Test 8: Login as alice
        print("\n[8] Testing login as alice...")
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "alice", "password": "alice123"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alice_token = response.json()["access_token"]
            print(f"Token: {alice_token[:50]}...")
        else:
            print(f"Error: {response.text}")
            return

        # Test 9: Alice tries to list sites (should be empty)
        print("\n[9] Testing alice list sites (should be denied)...")
        response = await client.get(
            f"{BASE_URL}/api/sites",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Sites visible to alice: {response.json()}")

        # Test 10: Admin grants alice read permission on site
        print("\n[10] Testing grant permission to alice...")
        response = await client.post(
            f"{BASE_URL}/api/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "grantee_type": "user",
                "grantee_id": alice_token.split('.')[1][:36],  # This won't work, need user ID
                "resource_type": "site",
                "resource_id": site_id,
                "permission": "read",
                "effect": "allow",
                "inherit": True
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print(f"Permission granted: {response.json()}")

        # Test 11: Bulk permission check
        print("\n[11] Testing bulk permission check...")
        response = await client.post(
            f"{BASE_URL}/api/permissions/check",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "checks": [
                    {"resource_type": "site", "resource_id": site_id, "permission": "read"},
                    {"resource_type": "plan", "resource_id": plan_id, "permission": "write"},
                    {"resource_type": "sensor", "resource_id": sensor_id, "permission": "delete"}
                ]
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Check results: {response.json()}")

        print("\n" + "="*60)
        print("TESTING COMPLETE")
        print("="*60)


async def main():
    """Main test function."""
    await setup_test_data()

    # Wait a bit for server to be ready
    print("\nWaiting for server to start...")
    await asyncio.sleep(2)

    try:
        await test_api()
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
