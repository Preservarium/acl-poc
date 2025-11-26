from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/acl_poc.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Admin credentials for initial setup
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Redis cache settings
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # Default TTL in seconds

    # Cache TTLs for different key patterns
    CACHE_TTL_PERMISSION: int = 300      # Permission check results (5 minutes)
    CACHE_TTL_USER_GROUPS: int = 600     # User group memberships (10 minutes)
    CACHE_TTL_ANCESTORS: int = 3600      # Resource ancestors (1 hour)

    # Scheduler settings
    ENABLE_SCHEDULER: bool = True
    PERMISSION_EXPIRY_CHECK_HOURS: int = 1  # Check every hour
    EXPIRY_NOTIFICATION_HOUR: int = 9  # Daily notification at 9 AM UTC
    EXPIRY_NOTIFICATION_DAYS: int = 7  # Notify 7 days in advance

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
