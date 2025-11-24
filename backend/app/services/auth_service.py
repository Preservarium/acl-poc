from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.

        Args:
            username: The username
            password: The plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def create_user(self, username: str, password: str, is_admin: bool = False) -> User:
        """
        Create a new user.

        Args:
            username: The username
            password: The plain text password
            is_admin: Whether the user is an admin

        Returns:
            Created User object
        """
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            is_admin=is_admin
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    @staticmethod
    def create_token(user: User) -> str:
        """
        Create an access token for a user.

        Args:
            user: The User object

        Returns:
            JWT access token
        """
        return create_access_token(data={"sub": user.id})

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            User object if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_users(self) -> list[User]:
        """
        Get all users.

        Returns:
            List of User objects
        """
        result = await self.db.execute(select(User))
        return list(result.scalars().all())
