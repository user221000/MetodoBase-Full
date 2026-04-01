"""
tests/test_rbac_permissions.py — Tests para el sistema RBAC.

Verifica:
- Jerarquía de roles
- Permisos por acción/recurso
- get_effective_gym_id para team members
- Aislamiento multi-tenant
"""
import pytest
from web.database.models import UserRole
from web.services.permissions import (
    has_permission,
    has_higher_or_equal_role,
    role_level,
    get_assignable_roles,
    ROLE_HIERARCHY,
)
from web.auth_deps import get_effective_gym_id


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def owner_user():
    """Usuario owner (tipo='gym')."""
    return {
        "id": "gym-001",
        "email": "owner@gym.com",
        "nombre": "Owner",
        "tipo": "gym",
        "role": "owner",
        "team_gym_id": None,
    }


@pytest.fixture
def admin_user():
    """Usuario admin (team member)."""
    return {
        "id": "admin-001",
        "email": "admin@gym.com",
        "nombre": "Admin",
        "tipo": "usuario",
        "role": "admin",
        "team_gym_id": "gym-001",
    }


@pytest.fixture
def nutriologo_user():
    """Usuario nutriólogo (team member)."""
    return {
        "id": "nutri-001",
        "email": "nutri@gym.com",
        "nombre": "Nutriólogo",
        "tipo": "usuario",
        "role": "nutriologo",
        "team_gym_id": "gym-001",
    }


@pytest.fixture
def viewer_user():
    """Usuario viewer (team member)."""
    return {
        "id": "viewer-001",
        "email": "viewer@gym.com",
        "nombre": "Viewer",
        "tipo": "usuario",
        "role": "viewer",
        "team_gym_id": "gym-001",
    }


# ══════════════════════════════════════════════════════════════════════════════
# ROLE HIERARCHY TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestRoleHierarchy:
    """Tests para la jerarquía de roles."""

    def test_role_levels_ordering(self):
        """OWNER > ADMIN > NUTRIOLOGO > VIEWER."""
        assert role_level(UserRole.OWNER) > role_level(UserRole.ADMIN)
        assert role_level(UserRole.ADMIN) > role_level(UserRole.NUTRIOLOGO)
        assert role_level(UserRole.NUTRIOLOGO) > role_level(UserRole.VIEWER)

    def test_owner_has_higher_role_than_all(self):
        """OWNER tiene rol mayor o igual a todos."""
        assert has_higher_or_equal_role(UserRole.OWNER, UserRole.OWNER)
        assert has_higher_or_equal_role(UserRole.OWNER, UserRole.ADMIN)
        assert has_higher_or_equal_role(UserRole.OWNER, UserRole.NUTRIOLOGO)
        assert has_higher_or_equal_role(UserRole.OWNER, UserRole.VIEWER)

    def test_viewer_has_lowest_role(self):
        """VIEWER solo tiene rol >= a sí mismo."""
        assert has_higher_or_equal_role(UserRole.VIEWER, UserRole.VIEWER)
        assert not has_higher_or_equal_role(UserRole.VIEWER, UserRole.NUTRIOLOGO)
        assert not has_higher_or_equal_role(UserRole.VIEWER, UserRole.ADMIN)
        assert not has_higher_or_equal_role(UserRole.VIEWER, UserRole.OWNER)


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION TESTS - CLIENTES
# ══════════════════════════════════════════════════════════════════════════════

class TestClientePermissions:
    """Tests para permisos de clientes."""

    def test_owner_can_crud_cliente(self, owner_user):
        """Owner puede crear, leer, actualizar y eliminar clientes."""
        assert has_permission(owner_user, "create", "cliente")
        assert has_permission(owner_user, "read", "cliente")
        assert has_permission(owner_user, "update", "cliente")
        assert has_permission(owner_user, "delete", "cliente")

    def test_nutriologo_can_create_read_update_cliente(self, nutriologo_user):
        """Nutriólogo puede crear, leer y actualizar, pero NO eliminar."""
        assert has_permission(nutriologo_user, "create", "cliente")
        assert has_permission(nutriologo_user, "read", "cliente")
        assert has_permission(nutriologo_user, "update", "cliente")
        assert not has_permission(nutriologo_user, "delete", "cliente")

    def test_viewer_can_only_read_cliente(self, viewer_user):
        """Viewer solo puede leer clientes."""
        assert has_permission(viewer_user, "read", "cliente")
        assert not has_permission(viewer_user, "create", "cliente")
        assert not has_permission(viewer_user, "update", "cliente")
        assert not has_permission(viewer_user, "delete", "cliente")


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION TESTS - PLANES
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanPermissions:
    """Tests para permisos de planes."""

    def test_nutriologo_can_create_plan(self, nutriologo_user):
        """Nutriólogo puede crear planes."""
        assert has_permission(nutriologo_user, "create", "plan")
        assert has_permission(nutriologo_user, "read", "plan")

    def test_viewer_cannot_create_plan(self, viewer_user):
        """Viewer no puede crear planes."""
        assert not has_permission(viewer_user, "create", "plan")
        assert has_permission(viewer_user, "read", "plan")


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION TESTS - TEAM
# ══════════════════════════════════════════════════════════════════════════════

class TestTeamPermissions:
    """Tests para permisos de gestión de equipo."""

    def test_owner_can_manage_team(self, owner_user):
        """Owner puede gestionar todo el equipo."""
        assert has_permission(owner_user, "read", "team")
        assert has_permission(owner_user, "invite", "team")
        assert has_permission(owner_user, "update_role", "team")
        assert has_permission(owner_user, "remove", "team")

    def test_admin_can_invite_but_not_change_roles(self, admin_user):
        """Admin puede invitar y eliminar, pero NO cambiar roles."""
        assert has_permission(admin_user, "read", "team")
        assert has_permission(admin_user, "invite", "team")
        assert not has_permission(admin_user, "update_role", "team")
        assert has_permission(admin_user, "remove", "team")

    def test_nutriologo_cannot_manage_team(self, nutriologo_user):
        """Nutriólogo no puede gestionar equipo."""
        assert not has_permission(nutriologo_user, "read", "team")
        assert not has_permission(nutriologo_user, "invite", "team")


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION TESTS - BILLING
# ══════════════════════════════════════════════════════════════════════════════

class TestBillingPermissions:
    """Tests para permisos de facturación."""

    def test_only_owner_can_manage_billing(self, owner_user, admin_user, nutriologo_user):
        """Solo Owner puede gestionar facturación."""
        assert has_permission(owner_user, "read", "billing")
        assert has_permission(owner_user, "update", "subscription")
        
        assert not has_permission(admin_user, "read", "billing")
        assert not has_permission(admin_user, "update", "subscription")
        
        assert not has_permission(nutriologo_user, "read", "billing")


# ══════════════════════════════════════════════════════════════════════════════
# EFFECTIVE GYM ID TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestEffectiveGymId:
    """Tests para get_effective_gym_id."""

    def test_owner_returns_own_id(self, owner_user):
        """Owner retorna su propio ID como gym_id."""
        assert get_effective_gym_id(owner_user) == "gym-001"

    def test_team_member_returns_team_gym_id(self, admin_user, nutriologo_user, viewer_user):
        """Team members retornan team_gym_id."""
        assert get_effective_gym_id(admin_user) == "gym-001"
        assert get_effective_gym_id(nutriologo_user) == "gym-001"
        assert get_effective_gym_id(viewer_user) == "gym-001"

    def test_legacy_gym_type_returns_own_id(self):
        """Usuario legacy con tipo='gym' retorna su propio ID."""
        legacy_user = {
            "id": "legacy-gym",
            "tipo": "gym",
            "role": None,  # Sin role explícito
            "team_gym_id": None,
        }
        assert get_effective_gym_id(legacy_user) == "legacy-gym"


# ══════════════════════════════════════════════════════════════════════════════
# ASSIGNABLE ROLES TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAssignableRoles:
    """Tests para roles asignables."""

    def test_owner_can_assign_all_roles_except_owner(self):
        """Owner puede asignar todos los roles excepto OWNER."""
        roles = get_assignable_roles(UserRole.OWNER)
        assert UserRole.ADMIN in roles
        assert UserRole.NUTRIOLOGO in roles
        assert UserRole.VIEWER in roles
        assert UserRole.OWNER not in roles

    def test_admin_can_assign_lower_roles(self):
        """Admin puede asignar NUTRIOLOGO y VIEWER."""
        roles = get_assignable_roles(UserRole.ADMIN)
        assert UserRole.NUTRIOLOGO in roles
        assert UserRole.VIEWER in roles
        assert UserRole.ADMIN not in roles
        assert UserRole.OWNER not in roles

    def test_nutriologo_cannot_assign_roles(self):
        """Nutriólogo no puede asignar roles."""
        roles = get_assignable_roles(UserRole.NUTRIOLOGO)
        assert len(roles) == 0


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-TENANT ISOLATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiTenantIsolation:
    """Tests para aislamiento multi-tenant."""

    def test_permission_denied_for_different_gym(self, nutriologo_user):
        """Permisos denegados para recursos de otro gym."""
        # Nutriólogo de gym-001 intenta acceder a recurso de gym-002
        assert not has_permission(
            nutriologo_user, 
            "read", 
            "cliente", 
            resource_owner_id="gym-002"
        )

    def test_permission_granted_for_same_gym(self, nutriologo_user):
        """Permisos otorgados para recursos del mismo gym."""
        assert has_permission(
            nutriologo_user,
            "read",
            "cliente",
            resource_owner_id="gym-001"
        )
