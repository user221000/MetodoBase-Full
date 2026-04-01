"""
tests/test_gym_repositories.py — Tests for SQLAlchemy gym repositories.

Validates:
1. GymSettings CRUD operations
2. GymLicense CRUD operations
3. Tenant isolation (gym_id filtering)
"""
import pytest
from datetime import datetime, timedelta, timezone
import uuid


class TestGymSettingsRepository:
    """Tests for gym_settings_repository functions."""

    def test_create_settings(self, test_gym_user):
        from web.repositories.gym_settings_repository import create_default_gym_settings
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            # Clean up first in case previous test left data
            from web.database.models import GymSettings
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

            settings = create_default_gym_settings(gym_id=gym_id, db=session)
            session.commit()

            assert settings.id is not None
            assert settings.gym_id == gym_id
            assert settings.trial_days == 14
            assert settings.timezone == "America/Mexico_City"

            # Cleanup
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

    def test_get_by_gym_id(self, test_gym_user):
        from web.repositories.gym_settings_repository import (
            create_default_gym_settings, get_gym_settings,
        )
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            from web.database.models import GymSettings
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

            created = create_default_gym_settings(
                gym_id=gym_id, trial_days=30, db=session,
            )
            session.commit()

            retrieved = get_gym_settings(gym_id, db=session)
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.trial_days == 30

            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

    def test_get_by_gym_id_returns_none_if_not_exists(self, test_gym_user):
        from web.repositories.gym_settings_repository import get_gym_settings
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        engine = get_engine()
        with SASession(engine) as session:
            settings = get_gym_settings(str(uuid.uuid4()), db=session)
            assert settings is None

    def test_update_settings(self, test_gym_user):
        from web.repositories.gym_settings_repository import (
            create_default_gym_settings, update_gym_settings,
        )
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            from web.database.models import GymSettings
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

            create_default_gym_settings(gym_id=gym_id, db=session)
            session.commit()

            updated = update_gym_settings(
                gym_id=gym_id,
                updates={"trial_days": 30, "timezone": "UTC"},
                db=session,
            )
            session.commit()

            assert updated is not None
            assert updated.trial_days == 30
            assert updated.timezone == "UTC"

            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

    def test_get_or_create(self, test_gym_user):
        from web.repositories.gym_settings_repository import get_or_create_gym_settings
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            from web.database.models import GymSettings
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()

            settings = get_or_create_gym_settings(gym_id=gym_id, db=session)
            session.commit()
            assert settings is not None
            assert settings.gym_id == gym_id

            session.query(GymSettings).filter(GymSettings.gym_id == gym_id).delete()
            session.commit()


class TestGymLicenseRepository:
    """Tests for gym_license_repository functions."""

    def test_create_license(self, test_gym_user):
        from web.repositories.gym_license_repository import create_license
        from web.database.engine import get_engine
        from web.database.models import GymLicense
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

            lic = create_license(
                gym_id=gym_id,
                plan_tier="premium",
                max_clients=100,
                db=session,
            )
            session.commit()

            assert lic is not None
            assert lic.gym_id == gym_id
            assert lic.plan_tier == "premium"

            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

    def test_get_active_license(self, test_gym_user):
        from web.repositories.gym_license_repository import (
            create_license, get_active_license,
        )
        from web.database.engine import get_engine
        from web.database.models import GymLicense
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

            create_license(
                gym_id=gym_id, plan_tier="standard", max_clients=25, db=session,
            )
            session.commit()

            active = get_active_license(gym_id, db=session)
            assert active is not None
            assert active.gym_id == gym_id

            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

    def test_check_license_valid(self, test_gym_user):
        from web.repositories.gym_license_repository import (
            create_license, check_license_valid,
        )
        from web.database.engine import get_engine
        from web.database.models import GymLicense
        from sqlalchemy.orm import Session as SASession

        gym_id = test_gym_user["id"]
        engine = get_engine()
        with SASession(engine) as session:
            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

            create_license(
                gym_id=gym_id, plan_tier="basic", max_clients=25, db=session,
            )
            session.commit()

            is_valid = check_license_valid(gym_id, db=session)
            assert is_valid is True

            session.query(GymLicense).filter(GymLicense.gym_id == gym_id).delete()
            session.commit()

    def test_no_license_returns_false(self):
        from web.repositories.gym_license_repository import check_license_valid
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SASession

        engine = get_engine()
        with SASession(engine) as session:
            is_valid = check_license_valid(str(uuid.uuid4()), db=session)
            assert is_valid is False


class TestTenantIsolation:
    """Tests para verificar tenant isolation en repositories."""

    def test_gym_settings_isolated_by_gym_id(self, test_gym_user):
        from web.repositories.gym_settings_repository import (
            create_default_gym_settings, get_gym_settings,
        )
        from web.database.engine import get_engine
        from web.database.models import GymSettings, Usuario
        from sqlalchemy.orm import Session as SASession

        gym_id_1 = test_gym_user["id"]
        gym_id_2 = str(uuid.uuid4())

        engine = get_engine()
        with SASession(engine) as session:
            # Clean up
            session.query(GymSettings).filter(GymSettings.gym_id == gym_id_1).delete()
            session.commit()

            # Create second user for FK
            existing = session.query(Usuario).filter(Usuario.id == gym_id_2).first()
            if not existing:
                session.add(Usuario(
                    id=gym_id_2,
                    email=f"iso_{gym_id_2[:8]}@test.com",
                    password_hash="not_a_real_hash",
                    nombre="Isolation Test",
                    tipo="gym",
                    role="owner",
                ))
                session.commit()

            create_default_gym_settings(
                gym_id=gym_id_1, trial_days=30, db=session,
            )
            create_default_gym_settings(
                gym_id=gym_id_2, trial_days=14, db=session,
            )
            session.commit()

            s1 = get_gym_settings(gym_id_1, db=session)
            s2 = get_gym_settings(gym_id_2, db=session)

            assert s1.trial_days == 30
            assert s2.trial_days == 14
            assert s1.id != s2.id

            # Cleanup
            session.query(GymSettings).filter(
                GymSettings.gym_id.in_([gym_id_1, gym_id_2])
            ).delete()
            session.commit()
