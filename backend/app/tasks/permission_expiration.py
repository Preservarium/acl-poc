"""
Permission expiration background task.

This module handles:
1. Expiring permissions that have passed their expiration date
2. Logging expiration events to the audit log
3. Sending notifications for permissions expiring soon
"""

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.permission import ResourcePermission
from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User
from app.models.group import Group

logger = logging.getLogger(__name__)


async def expire_permissions():
    """
    Find and handle expired permissions.

    This function:
    1. Finds all permissions where expires_at < now
    2. Logs each expiration to the audit log
    3. Optionally deletes or marks them as expired

    By default, expired permissions are deleted. If you want to keep them
    for historical purposes, you would need to add an 'is_expired' field
    to the ResourcePermission model.
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()

            # Find expired permissions
            result = await db.execute(
                select(ResourcePermission).where(
                    and_(
                        ResourcePermission.expires_at.isnot(None),
                        ResourcePermission.expires_at < now
                    )
                )
            )
            expired_perms = result.scalars().all()

            if not expired_perms:
                logger.info("No expired permissions found")
                return

            logger.info(f"Found {len(expired_perms)} expired permissions")

            # Process each expired permission
            for perm in expired_perms:
                try:
                    # Create audit log entry
                    audit_entry = AuditLog(
                        action=AuditAction.PERMISSION_EXPIRED,
                        actor_id=None,  # System action
                        target_user_id=perm.grantee_id if perm.grantee_type.value == "user" else None,
                        target_group_id=perm.grantee_id if perm.grantee_type.value == "group" else None,
                        resource_type=perm.resource_type.value,
                        resource_id=perm.resource_id,
                        permission=perm.permission.value,
                        details={
                            "grantee_type": perm.grantee_type.value,
                            "grantee_id": perm.grantee_id,
                            "effect": perm.effect.value,
                            "expired_at": perm.expires_at.isoformat(),
                            "granted_at": perm.granted_at.isoformat(),
                            "granted_by": perm.granted_by,
                        }
                    )
                    db.add(audit_entry)

                    # Delete the expired permission
                    await db.delete(perm)
                    await db.flush()

                    logger.info(
                        f"Expired permission: {perm.grantee_type.value}:{perm.grantee_id} "
                        f"on {perm.resource_type.value}:{perm.resource_id} "
                        f"(permission: {perm.permission.value})"
                    )

                except Exception as e:
                    logger.error(f"Error expiring permission {perm.id}: {str(e)}")
                    continue

            # Commit all changes
            await db.commit()
            logger.info(f"Successfully expired {len(expired_perms)} permissions")

        except Exception as e:
            logger.error(f"Error in expire_permissions task: {str(e)}")
            await db.rollback()
            raise


async def notify_expiring_permissions(days_ahead: int = 7):
    """
    Find permissions expiring soon and log notifications.

    Args:
        days_ahead: Number of days to look ahead for expiring permissions

    This function finds permissions expiring within the specified timeframe
    and logs them. In a production system, you would integrate with an email
    service or notification system here.
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()
            future_date = now + timedelta(days=days_ahead)

            # Find permissions expiring soon
            result = await db.execute(
                select(ResourcePermission).where(
                    and_(
                        ResourcePermission.expires_at.isnot(None),
                        ResourcePermission.expires_at > now,
                        ResourcePermission.expires_at <= future_date
                    )
                )
            )
            expiring_perms = result.scalars().all()

            if not expiring_perms:
                logger.info(f"No permissions expiring in the next {days_ahead} days")
                return

            logger.info(f"Found {len(expiring_perms)} permissions expiring in the next {days_ahead} days")

            # Group by grantee for notification purposes
            notifications = {}

            for perm in expiring_perms:
                grantee_key = f"{perm.grantee_type.value}:{perm.grantee_id}"

                if grantee_key not in notifications:
                    notifications[grantee_key] = {
                        "grantee_type": perm.grantee_type.value,
                        "grantee_id": perm.grantee_id,
                        "permissions": []
                    }

                days_until_expiry = (perm.expires_at - now).days
                notifications[grantee_key]["permissions"].append({
                    "permission_id": perm.id,
                    "resource_type": perm.resource_type.value,
                    "resource_id": perm.resource_id,
                    "permission": perm.permission.value,
                    "expires_at": perm.expires_at.isoformat(),
                    "days_until_expiry": days_until_expiry
                })

            # Log notifications (in production, send emails/notifications here)
            for grantee_key, notification in notifications.items():
                grantee_type = notification["grantee_type"]
                grantee_id = notification["grantee_id"]
                perm_count = len(notification["permissions"])

                # Get grantee name for logging
                grantee_name = "Unknown"
                if grantee_type == "user":
                    user_result = await db.execute(select(User).where(User.id == grantee_id))
                    user = user_result.scalar_one_or_none()
                    if user:
                        grantee_name = user.username
                elif grantee_type == "group":
                    group_result = await db.execute(select(Group).where(Group.id == grantee_id))
                    group = group_result.scalar_one_or_none()
                    if group:
                        grantee_name = group.name

                logger.info(
                    f"Notification: {grantee_type} '{grantee_name}' ({grantee_id}) "
                    f"has {perm_count} permission(s) expiring in the next {days_ahead} days"
                )

                # Log each permission
                for perm_info in notification["permissions"]:
                    logger.info(
                        f"  - {perm_info['permission']} on "
                        f"{perm_info['resource_type']}:{perm_info['resource_id']} "
                        f"(expires in {perm_info['days_until_expiry']} days)"
                    )

                # TODO: In production, integrate with notification service:
                # - Send email to users
                # - Send notification to group admins
                # - Create in-app notifications
                # Example:
                # await send_notification_email(
                #     grantee_type=grantee_type,
                #     grantee_id=grantee_id,
                #     permissions=notification["permissions"]
                # )

            logger.info(f"Processed notifications for {len(notifications)} grantees")

        except Exception as e:
            logger.error(f"Error in notify_expiring_permissions task: {str(e)}")
            raise


async def get_expiring_permissions(
    db: AsyncSession,
    days_ahead: int = 7
) -> List[ResourcePermission]:
    """
    Get list of permissions expiring within specified days.

    Args:
        db: Database session
        days_ahead: Number of days to look ahead

    Returns:
        List of ResourcePermission objects expiring soon
    """
    now = datetime.utcnow()
    future_date = now + timedelta(days=days_ahead)

    result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.expires_at.isnot(None),
                ResourcePermission.expires_at > now,
                ResourcePermission.expires_at <= future_date
            )
        ).order_by(ResourcePermission.expires_at)
    )

    return result.scalars().all()
