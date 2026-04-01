"""
web/sync_user.py — Legacy sync bridge (now no-op).

auth.py now writes directly to the SQLAlchemy usuarios table,
so syncing from a separate SQLite database is no longer needed.
These functions are kept as no-ops to avoid breaking callers.
"""
import logging

logger = logging.getLogger(__name__)


def sync_user_to_sa(usuario: dict) -> None:
    """No-op: auth.py now writes directly to the SQLAlchemy usuarios table."""
    pass


def sync_all_auth_users_to_sa() -> None:
    """No-op: auth.py now writes directly to the SQLAlchemy usuarios table."""
    pass
