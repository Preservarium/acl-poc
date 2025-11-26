"""
Tests for self-update business rules.

These tests verify that the SELF_UPDATE_RULES are properly enforced
when users attempt to modify their own account information.
"""

import pytest
from app.core.business_rules import (
    validate_self_update,
    get_allowed_self_update_fields,
    get_forbidden_self_update_fields,
    SELF_UPDATE_RULES
)
from fastapi import HTTPException


class TestSelfUpdateRules:
    """Test cases for self-update business rules."""

    def test_allowed_fields_list(self):
        """Test that allowed fields list is correct."""
        allowed = get_allowed_self_update_fields()
        assert allowed == ['email', 'password', 'first_name', 'last_name']

    def test_forbidden_fields_list(self):
        """Test that forbidden fields list is correct."""
        forbidden = get_forbidden_self_update_fields()
        assert forbidden == ['username', 'is_admin', 'disabled']

    def test_self_update_allowed_fields_as_user(self):
        """Test that non-admin users can update allowed fields."""
        # These should not raise exceptions
        validate_self_update({'email': 'new@example.com'}, is_admin=False)
        validate_self_update({'password': 'newpassword123'}, is_admin=False)
        validate_self_update({'first_name': 'John'}, is_admin=False)
        validate_self_update({'last_name': 'Doe'}, is_admin=False)
        validate_self_update({
            'email': 'new@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }, is_admin=False)

    def test_self_update_forbidden_username(self):
        """Test that non-admin users cannot update username."""
        with pytest.raises(HTTPException) as exc_info:
            validate_self_update({'username': 'newusername'}, is_admin=False)

        assert exc_info.value.status_code == 403
        assert "cannot modify 'username'" in exc_info.value.detail.lower()

    def test_self_update_forbidden_is_admin(self):
        """Test that non-admin users cannot update is_admin."""
        with pytest.raises(HTTPException) as exc_info:
            validate_self_update({'is_admin': True}, is_admin=False)

        assert exc_info.value.status_code == 403
        assert "cannot modify 'is_admin'" in exc_info.value.detail.lower()

    def test_self_update_forbidden_disabled(self):
        """Test that non-admin users cannot update disabled."""
        with pytest.raises(HTTPException) as exc_info:
            validate_self_update({'disabled': True}, is_admin=False)

        assert exc_info.value.status_code == 403
        assert "cannot modify 'disabled'" in exc_info.value.detail.lower()

    def test_self_update_mixed_allowed_and_forbidden(self):
        """Test that updates with both allowed and forbidden fields fail."""
        with pytest.raises(HTTPException) as exc_info:
            validate_self_update({
                'email': 'new@example.com',
                'username': 'newusername'
            }, is_admin=False)

        assert exc_info.value.status_code == 403

    def test_admin_can_update_all_fields(self):
        """Test that admins can update any field on themselves."""
        # Admins should be able to update forbidden fields
        validate_self_update({'username': 'newusername'}, is_admin=True)
        validate_self_update({'is_admin': False}, is_admin=True)
        validate_self_update({'disabled': True}, is_admin=True)
        validate_self_update({
            'username': 'newusername',
            'email': 'new@example.com',
            'is_admin': False,
            'disabled': True
        }, is_admin=True)

    def test_empty_updates(self):
        """Test that empty updates don't raise exceptions."""
        validate_self_update({}, is_admin=False)
        validate_self_update({}, is_admin=True)

    def test_rules_constants(self):
        """Test that SELF_UPDATE_RULES constant is properly defined."""
        assert 'allowed' in SELF_UPDATE_RULES
        assert 'forbidden' in SELF_UPDATE_RULES
        assert len(SELF_UPDATE_RULES['allowed']) == 4
        assert len(SELF_UPDATE_RULES['forbidden']) == 3


# Integration test examples (these would require database setup)
class TestSelfUpdateIntegration:
    """
    Integration tests for self-update functionality.

    Note: These are example test structures. Actual implementation would
    require database fixtures and API client setup.
    """

    # Example test structure - would need proper fixtures
    async def test_user_updates_own_email(self):
        """Test that a user can update their own email."""
        # This would use a test client to PUT /users/{id} with email update
        # Assert response is 200 and email is updated
        pass

    async def test_user_cannot_update_own_username(self):
        """Test that a user cannot update their own username."""
        # This would use a test client to PUT /users/{id} with username update
        # Assert response is 403 with appropriate error message
        pass

    async def test_admin_updates_own_username(self):
        """Test that an admin can update their own username."""
        # This would use a test client to PUT /users/{id} with username update
        # Assert response is 200 and username is updated
        pass

    async def test_user_updates_another_user_with_permission(self):
        """Test that a user with write permission can update another user."""
        # Grant write permission to user A on user B
        # User A updates user B's email
        # Assert response is 200 and email is updated
        pass

    async def test_user_cannot_update_another_user_without_permission(self):
        """Test that a user without permission cannot update another user."""
        # User A attempts to update user B without permission
        # Assert response is 403
        pass

    async def test_field_level_permissions(self):
        """Test that field-level ACL restrictions are enforced."""
        # Grant write permission with fields=['email'] to user A on user B
        # User A can update email but not first_name
        # Assert email update succeeds, first_name update fails
        pass
