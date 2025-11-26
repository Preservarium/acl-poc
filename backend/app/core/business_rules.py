"""
Business rules module.

This module contains business logic and validation rules that are separate from
ACL (Access Control List) permissions. These rules enforce domain-specific constraints
that apply regardless of permission settings.
"""

from typing import Dict, Any, List
from fastapi import HTTPException, status


SELF_UPDATE_RULES = {
    'allowed': ['email', 'password', 'first_name', 'last_name'],
    'forbidden': ['username', 'is_admin', 'disabled'],
}


def validate_self_update(updates: Dict[str, Any], is_admin: bool = False) -> None:
    """
    Validate that a user is not trying to modify forbidden fields on themselves.

    This implements the business rule that non-admin users cannot modify certain
    privileged fields on their own account (username, is_admin, disabled).
    Admins can modify any field on any account, including their own.

    Args:
        updates: Dictionary of fields being updated
        is_admin: Whether the user is a system admin (admins bypass this check)

    Raises:
        HTTPException: If user attempts to modify forbidden fields

    Example:
        >>> validate_self_update({'email': 'new@example.com'}, is_admin=False)
        # No error - email is allowed

        >>> validate_self_update({'username': 'newname'}, is_admin=False)
        # Raises HTTPException - username is forbidden

        >>> validate_self_update({'username': 'newname'}, is_admin=True)
        # No error - admins can modify anything
    """
    if is_admin:
        return  # Admins can modify anything

    for field in updates.keys():
        if field in SELF_UPDATE_RULES['forbidden']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot modify '{field}' on your own account"
            )


def get_allowed_self_update_fields() -> List[str]:
    """
    Return list of fields a non-admin user can modify on themselves.

    Returns:
        List of allowed field names

    Example:
        >>> get_allowed_self_update_fields()
        ['email', 'password', 'first_name', 'last_name']
    """
    return SELF_UPDATE_RULES['allowed']


def get_forbidden_self_update_fields() -> List[str]:
    """
    Return list of fields a non-admin user cannot modify on themselves.

    Returns:
        List of forbidden field names

    Example:
        >>> get_forbidden_self_update_fields()
        ['username', 'is_admin', 'disabled']
    """
    return SELF_UPDATE_RULES['forbidden']
