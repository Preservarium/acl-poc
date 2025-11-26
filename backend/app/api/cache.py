"""Cache management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.core.dependencies import get_current_user
from app.services.cache_service import cache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get cache statistics.

    Requires admin privileges.

    Returns:
    - enabled: Whether cache is enabled
    - connected: Whether connected to Redis
    - hits: Number of cache hits
    - misses: Number of cache misses
    - sets: Number of cache sets
    - deletes: Number of cache deletes
    - errors: Number of cache errors
    - hit_rate: Cache hit rate percentage
    - total_requests: Total cache requests
    - memory: Redis memory usage information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view cache statistics"
        )

    # Get basic stats
    stats = cache.get_stats()

    # Get memory info if available
    memory_info = await cache.get_memory_info()
    if memory_info:
        stats["memory"] = memory_info

    return stats


@router.post("/clear/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_user_cache(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Clear all cached permissions for a specific user.

    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear cache"
        )

    await cache.invalidate_user_permissions(user_id)


@router.post("/clear/resource/{resource_type}/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_resource_cache(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Clear all cached permissions for a specific resource.

    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear cache"
        )

    await cache.invalidate_resource_permissions(resource_type, resource_id)


@router.post("/clear/all", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_cache(
    current_user: User = Depends(get_current_user),
):
    """
    Clear all cached data.

    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear cache"
        )

    # Clear all permission-related caches
    await cache.delete_pattern("perm:*")
    await cache.delete_pattern("user_groups:*")
    await cache.delete_pattern("ancestors:*")
