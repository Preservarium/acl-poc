"""
Hierarchy configuration and traversal for ACL system.
ACL reads hierarchy from business tables via this config.
"""

from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Hierarchy configuration - defines parent-child relationships
HIERARCHY_CONFIG = {
    # Hierarchical resources (permissions inherit down)
    'alert': {'parent_type': 'alarm', 'parent_fk': 'alarm_id'},
    'alarm': {'parent_type': 'sensor', 'parent_fk': 'sensor_id'},
    'sensor': {'parent_type': 'plan', 'parent_fk': 'plan_id'},
    'broker': {'parent_type': 'plan', 'parent_fk': 'plan_id'},
    'plan': {'parent_type': 'site', 'parent_fk': 'site_id'},
    'site': {'parent_type': None, 'parent_fk': None},  # root

    # Standalone resources (no inheritance)
    'group': {'parent_type': None, 'parent_fk': None},
    'user': {'parent_type': None, 'parent_fk': None},
    'dashboard': {'parent_type': None, 'parent_fk': None},
}

# Map resource types to their model classes
def get_model_class(resource_type: str):
    """Get SQLAlchemy model class for resource type."""
    from app.models import Site, Plan, Sensor, Group, Broker, Alarm, Alert, Dashboard, User

    model_map = {
        'site': Site,
        'plan': Plan,
        'sensor': Sensor,
        'broker': Broker,
        'alarm': Alarm,
        'alert': Alert,
        'dashboard': Dashboard,
        'group': Group,
        'user': User,
    }

    return model_map.get(resource_type)


async def get_ancestors(
    db: AsyncSession,
    resource_type: str,
    resource_id: str
) -> List[Tuple[str, str, int]]:
    """
    Walk up hierarchy using HIERARCHY_CONFIG.
    Standalone resources return only themselves.

    Returns: List of (resource_type, resource_id, depth) tuples
             depth=0 is the resource itself, depth increases going up
    """
    config = HIERARCHY_CONFIG.get(resource_type)

    # Unknown resource type
    if config is None:
        return []

    # Standalone resource - no ancestors
    if config['parent_type'] is None:
        return [(resource_type, resource_id, 0)]

    ancestors = [(resource_type, resource_id, 0)]
    current_type = resource_type
    current_id = resource_id
    depth = 1

    while True:
        cfg = HIERARCHY_CONFIG.get(current_type)
        if not cfg or not cfg['parent_type']:
            break

        # Get the model class for current resource
        model_class = get_model_class(current_type)
        if not model_class:
            break

        # Query the resource to get parent ID
        result = await db.execute(
            select(model_class).where(model_class.id == current_id)
        )
        resource = result.scalar_one_or_none()

        if not resource:
            break

        # Get parent ID from the foreign key column
        parent_id = getattr(resource, cfg['parent_fk'], None)
        if not parent_id:
            break

        # Add parent to ancestors
        ancestors.append((cfg['parent_type'], parent_id, depth))
        current_type = cfg['parent_type']
        current_id = parent_id
        depth += 1

    return ancestors


def is_hierarchical(resource_type: str) -> bool:
    """Check if resource type participates in hierarchy (can inherit permissions)."""
    config = HIERARCHY_CONFIG.get(resource_type)
    return config is not None and config['parent_type'] is not None


def is_standalone(resource_type: str) -> bool:
    """Check if resource type is standalone (no inheritance)."""
    config = HIERARCHY_CONFIG.get(resource_type)
    return config is not None and config['parent_type'] is None


def get_parent_info(resource_type: str) -> Optional[Tuple[str, str]]:
    """Get parent type and FK column name for a resource type."""
    config = HIERARCHY_CONFIG.get(resource_type)
    if config and config['parent_type']:
        return (config['parent_type'], config['parent_fk'])
    return None
