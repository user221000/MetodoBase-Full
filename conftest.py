"""
conftest.py — Auto-adds the project root to sys.path so that
`pytest tests/` works without setting PYTHONPATH explicitly.
Also configures test environment settings.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

# Insert project root at the front of sys.path
sys.path.insert(0, str(Path(__file__).parent))

# ── Test Environment Settings ────────────────────────────────────────────────
# Disable rate limiting during tests to prevent 429 responses
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
# Disable metrics collection during tests to reduce overhead
os.environ.setdefault("METRICS_ENABLED", "false")
# Disable alerting during tests to prevent spam
os.environ.setdefault("ALERT_ENABLED", "false")


# ── Auth Fixtures for API Tests ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_gym_user():
    """
    Creates a test gym user and returns credentials for API authentication.
    Returns dict with: id, email, nombre, tipo, access_token, auth_headers
    """
    from web.auth import init_auth, crear_access_token, hash_password
    from web.database.engine import init_db, get_engine
    from web.database.models import Usuario
    from sqlalchemy.orm import Session as SQLASession
    import time
    from datetime import datetime, timezone
    
    init_auth()
    init_db()  # Initialize SQLAlchemy DB
    
    uid = str(uuid.uuid4())
    email = f"test_gym_{uid[:8]}@test.com"
    now_dt = datetime.now(timezone.utc)
    
    # Create user in SQLAlchemy usuarios table (auth.py now uses this directly)
    engine = get_engine()
    with SQLASession(engine) as session:
        try:
            existing = session.query(Usuario).filter(Usuario.id == uid).first()
            if not existing:
                usuario_sa = Usuario(
                    id=uid,
                    email=email,
                    password_hash=hash_password("test123"),
                    nombre="Test Gym",
                    apellido="",
                    tipo="gym",
                    activo=True,
                    fecha_registro=now_dt,
                )
                session.add(usuario_sa)
                session.commit()
        except Exception:
            session.rollback()
    
    user = {
        "id": uid,
        "email": email,
        "nombre": "Test Gym",
        "tipo": "gym",
    }
    
    access_token = crear_access_token(user)
    
    return {
        **user,
        "access_token": access_token,
        "auth_headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="module")
def auth_client(test_gym_user):
    """
    Returns a TestClient with pre-configured Authorization headers.
    Use this for tests that require authentication.
    """
    from fastapi.testclient import TestClient
    from api.app import create_app
    
    app = create_app()
    
    class AuthenticatedTestClient(TestClient):
        def __init__(self, *args, auth_headers=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._auth_headers = auth_headers or {}
        
        def request(self, method, url, **kwargs):
            headers = kwargs.get("headers") or {}
            # Merge auth headers with any custom headers
            merged = {**self._auth_headers, **headers}
            kwargs["headers"] = merged
            return super().request(method, url, **kwargs)
    
    with AuthenticatedTestClient(
        app, 
        raise_server_exceptions=False,
        auth_headers=test_gym_user["auth_headers"],
    ) as c:
        yield c
