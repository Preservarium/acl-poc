"""Redis cache service for ACL system."""

import json
import logging
from typing import Optional, Any, List
from redis import asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based cache service with graceful fallback.

    Implements caching for:
    - Permission check results
    - User group memberships
    - Resource ancestor chains

    Key patterns:
    - perm:{user_id}:{resource_type}:{resource_id}:{perm}
    - user_groups:{user_id}
    - ancestors:{resource_type}:{resource_id}
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._enabled = settings.CACHE_ENABLED
        self._connected = False

        # Stats tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

    async def connect(self) -> None:
        """Initialize Redis connection."""
        if not self._enabled:
            logger.info("Cache is disabled via configuration")
            return

        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self.redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except (RedisError, ConnectionError) as e:
            self._connected = False
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self.redis = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    def is_available(self) -> bool:
        """Check if cache is available."""
        return self._enabled and self._connected and self.redis is not None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or unavailable
        """
        if not self.is_available():
            return None

        try:
            value = await self.redis.get(key)
            if value is not None:
                self._stats["hits"] += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                self._stats["misses"] += 1
                logger.debug(f"Cache MISS: {key}")
                return None
        except (RedisError, json.JSONDecodeError) as e:
            self._stats["errors"] += 1
            logger.error(f"Cache GET error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (None = use default)

        Returns:
            True if set successfully, False otherwise
        """
        if not self.is_available():
            return False

        try:
            ttl = ttl or settings.CACHE_TTL
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            self._stats["sets"] += 1
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError, ValueError) as e:
            self._stats["errors"] += 1
            logger.error(f"Cache SET error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available():
            return False

        try:
            deleted = await self.redis.delete(key)
            self._stats["deletes"] += 1
            logger.debug(f"Cache DELETE: {key}")
            return deleted > 0
        except RedisError as e:
            self._stats["errors"] += 1
            logger.error(f"Cache DELETE error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "perm:user123:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0

        try:
            # Scan for matching keys
            keys = []
            cursor = 0
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(partial_keys)
                if cursor == 0:
                    break

            # Delete all matching keys
            if keys:
                deleted = await self.redis.delete(*keys)
                self._stats["deletes"] += deleted
                logger.debug(f"Cache DELETE PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except RedisError as e:
            self._stats["errors"] += 1
            logger.error(f"Cache DELETE PATTERN error for {pattern}: {e}")
            return 0

    # Cache key builders for specific patterns

    def make_permission_key(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: str
    ) -> str:
        """Build cache key for permission check result."""
        return f"perm:{user_id}:{resource_type}:{resource_id}:{permission}"

    def make_user_groups_key(self, user_id: str) -> str:
        """Build cache key for user group memberships."""
        return f"user_groups:{user_id}"

    def make_ancestors_key(self, resource_type: str, resource_id: str) -> str:
        """Build cache key for resource ancestors."""
        return f"ancestors:{resource_type}:{resource_id}"

    # High-level cache operations for specific use cases

    async def get_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: str
    ) -> Optional[tuple]:
        """
        Get cached permission check result.

        Returns:
            Tuple of (allowed: bool, fields: Optional[List[str]]) or None
        """
        key = self.make_permission_key(user_id, resource_type, resource_id, permission)
        result = await self.get(key)
        if result is not None:
            return (result["allowed"], result["fields"])
        return None

    async def set_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: str,
        allowed: bool,
        fields: Optional[List[str]] = None
    ) -> bool:
        """Cache permission check result."""
        key = self.make_permission_key(user_id, resource_type, resource_id, permission)
        value = {"allowed": allowed, "fields": fields}
        return await self.set(key, value, ttl=settings.CACHE_TTL_PERMISSION)

    async def get_user_groups(self, user_id: str) -> Optional[List[str]]:
        """Get cached user group memberships."""
        key = self.make_user_groups_key(user_id)
        return await self.get(key)

    async def set_user_groups(self, user_id: str, group_ids: List[str]) -> bool:
        """Cache user group memberships."""
        key = self.make_user_groups_key(user_id)
        return await self.set(key, group_ids, ttl=settings.CACHE_TTL_USER_GROUPS)

    async def get_ancestors(
        self,
        resource_type: str,
        resource_id: str
    ) -> Optional[List[tuple]]:
        """Get cached resource ancestors."""
        key = self.make_ancestors_key(resource_type, resource_id)
        result = await self.get(key)
        if result is not None:
            # Convert back to tuples
            return [tuple(item) for item in result]
        return None

    async def set_ancestors(
        self,
        resource_type: str,
        resource_id: str,
        ancestors: List[tuple]
    ) -> bool:
        """Cache resource ancestors."""
        key = self.make_ancestors_key(resource_type, resource_id)
        # Convert tuples to lists for JSON serialization
        serializable = [list(item) for item in ancestors]
        return await self.set(key, serializable, ttl=settings.CACHE_TTL_ANCESTORS)

    async def invalidate_user_permissions(self, user_id: str) -> int:
        """
        Invalidate all cached permissions for a user.

        Called when user's permissions or group memberships change.
        """
        count = 0
        # Invalidate permission checks
        count += await self.delete_pattern(f"perm:{user_id}:*")
        # Invalidate group memberships
        count += await self.delete(self.make_user_groups_key(user_id))
        return count

    async def invalidate_resource_permissions(
        self,
        resource_type: str,
        resource_id: str
    ) -> int:
        """
        Invalidate all cached permissions for a resource.

        Called when permissions on a resource change.
        """
        count = 0
        # Invalidate permission checks for this resource
        count += await self.delete_pattern(f"perm:*:{resource_type}:{resource_id}:*")
        # Invalidate ancestors cache
        count += await self.delete(self.make_ancestors_key(resource_type, resource_id))
        return count

    async def invalidate_group_permissions(self, group_id: str) -> int:
        """
        Invalidate cached permissions for all users in a group.

        Called when group permissions change.
        This is a coarse invalidation - we clear all permission checks.
        """
        # Since we don't track group->users mapping in cache,
        # we need to invalidate all permission checks
        return await self.delete_pattern("perm:*")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, sets, deletes, errors, and hit rate
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0.0
        )

        return {
            "enabled": self._enabled,
            "connected": self._connected,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "errors": self._stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }

    async def get_memory_info(self) -> Optional[dict]:
        """
        Get Redis memory usage information.

        Returns:
            Dict with memory stats or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            info = await self.redis.info("memory")
            return {
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_peak": info.get("used_memory_peak"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "maxmemory": info.get("maxmemory"),
                "maxmemory_human": info.get("maxmemory_human"),
            }
        except RedisError as e:
            logger.error(f"Failed to get memory info: {e}")
            return None


# Global cache service instance
cache = CacheService()
