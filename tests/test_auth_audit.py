"""
tests/test_auth_audit.py — Tests for auth audit log service.

Validates:
1. log_auth_event creates audit log entries
2. get_recent_login_attempts filters by gym and time window
3. get_login_stats computes aggregates correctly
4. Request ID is captured correctly
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock
import uuid


class TestLogAuthEvent:
    """Tests for log_auth_event function."""
    
    @pytest.mark.asyncio
    async def test_log_auth_event_creates_entry(self, test_gym_user):
        """log_auth_event debe crear una entrada en auth_audit_log."""
        from web.services.auth_audit import log_auth_event, AuthEventType
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession
        from web.database.models import AuthAuditLog
        
        gym_id = test_gym_user["id"]
        request_id = uuid.uuid4().hex[:12]
        
        # Log an event (sync function, no await)
        log_auth_event(
            event_type=AuthEventType.LOGIN_SUCCESS,
            gym_id=gym_id,
            user_id=gym_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            request_id=request_id,
            metadata={"test": "data"}
        )
        
        # Verify entry was created
        engine = get_engine()
        with SASession(engine) as session:
            log_entry = session.query(AuthAuditLog).filter(
                AuthAuditLog.request_id == request_id
            ).first()
            
            assert log_entry is not None, "Log entry was not created"
            assert log_entry.event_type == AuthEventType.LOGIN_SUCCESS.value
            assert log_entry.gym_id == gym_id
            assert log_entry.user_id == gym_id
            assert log_entry.ip_address == "192.168.1.100"
            assert log_entry.user_agent == "Mozilla/5.0"
            assert log_entry.event_metadata["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_log_auth_event_handles_missing_fields(self):
        """log_auth_event debe funcionar con campos opcionales null."""
        from web.services.auth_audit import log_auth_event, AuthEventType
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession
        from web.database.models import AuthAuditLog
        
        request_id = uuid.uuid4().hex[:12]
        
        # Log without user_id (failed login) — sync function, no await
        log_auth_event(
            event_type=AuthEventType.LOGIN_FAILED,
            gym_id=None,
            ip_address="192.168.1.100",
            user_agent="curl/7.68.0",
            request_id=request_id,
            metadata={"reason": "invalid_credentials"}
        )
        
        # Verify entry was created
        engine = get_engine()
        with SASession(engine) as session:
            log_entry = session.query(AuthAuditLog).filter(
                AuthAuditLog.request_id == request_id
            ).first()
            
            assert log_entry is not None
            assert log_entry.event_type == AuthEventType.LOGIN_FAILED.value
            assert log_entry.user_id is None
            assert log_entry.event_metadata["reason"] == "invalid_credentials"


class TestGetRecentLoginAttempts:
    """Tests for get_recent_login_attempts function."""
    
    @pytest.mark.asyncio
    async def test_filters_by_email(self, test_gym_user):
        """get_recent_login_attempts debe filtrar por email."""
        from web.services.auth_audit import log_auth_event, get_recent_login_attempts, AuthEventType
        
        gym_id = test_gym_user["id"]
        email = test_gym_user["email"]
        
        # Log a failed login event with email in metadata
        log_auth_event(
            AuthEventType.LOGIN_FAILED,
            gym_id=gym_id,
            ip_address="192.168.1.1",
            metadata={"email": email, "reason": "invalid_password"}
        )
        
        # get_recent_login_attempts filters by email in JSON metadata
        attempts = get_recent_login_attempts(email=email, since_minutes=60)
        
        assert len(attempts) >= 1, "Should find at least one attempt"
    
    @pytest.mark.asyncio
    async def test_filters_by_time_window(self, test_gym_user):
        """get_recent_login_attempts debe filtrar por ventana de tiempo."""
        from web.services.auth_audit import get_recent_login_attempts
        from web.database.engine import get_engine
        from web.database.models import AuthAuditLog
        from sqlalchemy.orm import Session as SASession
        
        gym_id = test_gym_user["id"]
        email = test_gym_user["email"]
        
        # Create an old log entry (2 hours ago)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        engine = get_engine()
        
        with SASession(engine) as session:
            old_log = AuthAuditLog(
                id=str(uuid.uuid4()),
                event_type="login_failed",
                gym_id=gym_id,
                user_id=gym_id,
                ip_address="192.168.1.1",
                created_at=old_time,
                event_metadata={"email": email}
            )
            session.add(old_log)
            session.commit()
        
        # Get attempts from last 15 min (should NOT include 2-hour-old log)
        attempts = get_recent_login_attempts(email=email, since_minutes=15)
        
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15)
        for a in attempts:
            ts = a.created_at.replace(tzinfo=None) if a.created_at.tzinfo else a.created_at
            assert ts >= cutoff, f"Log entry {ts} is older than cutoff {cutoff}"


class TestGetLoginStats:
    """Tests for get_login_stats_for_gym function."""
    
    @pytest.mark.asyncio
    async def test_computes_success_and_failure_counts(self, test_gym_user):
        """get_login_stats_for_gym debe contar logins exitosos y fallidos."""
        from web.services.auth_audit import log_auth_event, get_login_stats_for_gym, AuthEventType
        
        gym_id = test_gym_user["id"]
        request_id_base = uuid.uuid4().hex[:8]
        
        # Log 3 successful + 2 failed logins
        for i in range(3):
            log_auth_event(
                AuthEventType.LOGIN_SUCCESS,
                gym_id=gym_id,
                user_id=gym_id,
                ip_address="192.168.1.1",
                request_id=f"{request_id_base}_success_{i}"
            )
        
        for i in range(2):
            log_auth_event(
                AuthEventType.LOGIN_FAILED,
                gym_id=gym_id,
                ip_address="192.168.1.1",
                request_id=f"{request_id_base}_failed_{i}"
            )
        
        # Get stats
        stats = get_login_stats_for_gym(gym_id=gym_id, since_days=1)
        
        assert stats["total_logins"] >= 3
        assert stats["failed_logins"] >= 2
    
    @pytest.mark.asyncio
    async def test_counts_unique_ips(self, test_gym_user):
        """get_login_stats_for_gym debe contar IPs únicas."""
        from web.services.auth_audit import log_auth_event, get_login_stats_for_gym, AuthEventType
        
        gym_id = test_gym_user["id"]
        request_id_base = uuid.uuid4().hex[:8]
        
        # Log from 3 different IPs
        ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        for i, ip in enumerate(ips):
            log_auth_event(
                AuthEventType.LOGIN_SUCCESS,
                gym_id=gym_id,
                user_id=gym_id,
                ip_address=ip,
                request_id=f"{request_id_base}_ip_{i}"
            )
        
        stats = get_login_stats_for_gym(gym_id=gym_id, since_days=1)
        
        assert stats["unique_ips"] >= 3, f"Expected >=3 unique IPs, got {stats['unique_ips']}"


class TestLogAuthEventFromRequest:
    """Tests for log_auth_event_from_request helper."""
    
    @pytest.mark.asyncio
    async def test_extracts_request_id_from_state(self, test_gym_user):
        """log_auth_event_from_request debe extraer request_id del request.state."""
        from web.services.auth_audit import log_auth_event_from_request, AuthEventType
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession
        from web.database.models import AuthAuditLog
        
        # Mock request
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.50"
        request.headers = {"user-agent": "TestAgent/1.0"}
        request_id = uuid.uuid4().hex[:12]
        request.state = Mock()
        request.state.request_id = request_id
        
        gym_id = test_gym_user["id"]
        
        # Log event
        await log_auth_event_from_request(
            event_type=AuthEventType.TOKEN_REFRESH,
            request=request,
            gym_id=gym_id,
            user_id=gym_id,
        )
        
        # Verify request_id was captured
        engine = get_engine()
        with SASession(engine) as session:
            log_entry = session.query(AuthAuditLog).filter(
                AuthAuditLog.request_id == request_id
            ).first()
            
            assert log_entry is not None
            assert log_entry.request_id == request_id
            assert log_entry.ip_address == "192.168.1.50"
            assert log_entry.user_agent == "TestAgent/1.0"
    
    @pytest.mark.asyncio
    async def test_handles_missing_request_id(self, test_gym_user):
        """log_auth_event_from_request debe funcionar sin request_id."""
        from web.services.auth_audit import log_auth_event_from_request, AuthEventType
        
        # Mock request without request_id
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.50"
        request.headers = {"user-agent": "TestAgent/1.0"}
        request.state = Mock()
        # No request_id attribute
        
        gym_id = test_gym_user["id"]
        
        # Should not raise exception
        await log_auth_event_from_request(
            event_type=AuthEventType.LOGIN_SUCCESS,
            request=request,
            gym_id=gym_id,
            user_id=gym_id,
        )


class TestAuthEventTypeEnum:
    """Tests for AuthEventType enum."""
    
    def test_all_event_types_defined(self):
        """Verificar que todos los tipos de eventos están definidos."""
        from web.services.auth_audit import AuthEventType
        
        # Verificar que los eventos principales existen
        expected_types = [
            "LOGIN_SUCCESS",
            "LOGIN_FAILED",
            "LOGOUT",
            "TOKEN_REFRESH",
        ]
        
        for event_type in expected_types:
            assert hasattr(AuthEventType, event_type), f"Missing event type: {event_type}"
    
    def test_enum_values_are_lowercase(self):
        """Los valores del enum deben ser lowercase (formato DB)."""
        from web.services.auth_audit import AuthEventType
        
        for event in AuthEventType:
            assert event.value.islower(), f"Event type {event.name} value should be lowercase: {event.value}"


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestAuditIntegration:
    """Integration tests con endpoints reales."""
    
    def test_login_creates_audit_log(self, test_gym_user):
        """Login endpoint debe crear entrada de audit log."""
        from fastapi.testclient import TestClient
        from web.main_web import create_app
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession
        from web.database.models import AuthAuditLog
        
        app = create_app()
        client = TestClient(app)
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_gym_user["email"],
                "password": "test123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 200
        
        # Verify audit log was created
        engine = get_engine()
        with SASession(engine) as session:
            logs = session.query(AuthAuditLog).filter(
                AuthAuditLog.gym_id == test_gym_user["id"],
                AuthAuditLog.event_type == "login_success"
            ).order_by(AuthAuditLog.created_at.desc()).limit(1).all()
            
            assert len(logs) > 0, "No audit log created for successful login"
            
            latest_log = logs[0]
            assert latest_log.user_id == test_gym_user["id"]
            assert latest_log.ip_address is not None
