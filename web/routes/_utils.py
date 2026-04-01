"""web/routes/_utils.py — Shared utilities for web route modules."""
from web.auth_deps import get_effective_gym_id


def get_gym_id(usuario: dict) -> str:
    """Get effective gym_id supporting team members."""
    return get_effective_gym_id(usuario)
