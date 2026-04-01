"""
web/services — Business logic services for MetodoBase Web.

Available services:
- email_service: Email sending (templates, transactional)
- feature_gate: Feature flag checking
- stripe_service: Stripe payment integration
- permissions: RBAC permission system
"""
from .permissions import (
    has_permission,
    verify_permission,
    require_role,
    require_min_role,
    require_permission,
    require_owner,
    require_admin_or_owner,
    get_role_display_name,
    get_assignable_roles,
    can_manage_user,
    ROLE_HIERARCHY,
    PERMISSIONS,
    UserRole,
)

__all__ = [
    # Permissions
    "has_permission",
    "verify_permission",
    "require_role",
    "require_min_role",
    "require_permission",
    "require_owner",
    "require_admin_or_owner",
    "get_role_display_name",
    "get_assignable_roles",
    "can_manage_user",
    "ROLE_HIERARCHY",
    "PERMISSIONS",
    "UserRole",
]
