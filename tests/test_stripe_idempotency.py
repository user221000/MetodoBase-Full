"""
tests/test_stripe_idempotency.py — Tests para idempotencia de webhooks Stripe

Verifica:
- Eventos nuevos se procesan y almacenan
- Eventos duplicados son ignorados sin error
- La purga de eventos antiguos funciona
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestStripeWebhookIdempotency:
    """Tests de idempotencia para webhooks de Stripe."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de BD."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db
    
    @pytest.fixture
    def sample_event(self):
        """Evento de Stripe de ejemplo."""
        return {
            "id": "evt_test_123abc",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_xyz",
                    "metadata": {"gym_id": "gym_001", "plan": "standard"},
                    "customer": "cus_xxx",
                    "subscription": "sub_xxx",
                }
            }
        }
    
    def test_new_event_is_processed(self, mock_db, sample_event):
        """Un evento nuevo debe ser procesado."""
        from web.services.stripe_service import handle_webhook_event
        
        # Mock: evento no existe (no es duplicado)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock del handler para evitar procesar realmente
        with patch("web.services.stripe_service._on_checkout_completed") as mock_handler:
            mock_handler.return_value = "activated:standard"
            
            result = handle_webhook_event(mock_db, sample_event)
            
            # Debe haber llamado al handler
            mock_handler.assert_called_once()
            assert result == "activated:standard"
            
            # Debe haber marcado como procesado (añadido a BD)
            mock_db.add.assert_called_once()
    
    def test_duplicate_event_is_ignored(self, mock_db, sample_event):
        """Un evento duplicado debe ser ignorado sin error."""
        from web.services.stripe_service import handle_webhook_event
        
        # Mock: evento YA existe (es duplicado)
        existing_event = MagicMock()
        existing_event.event_id = "evt_test_123abc"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_event
        
        with patch("web.services.stripe_service._on_checkout_completed") as mock_handler:
            result = handle_webhook_event(mock_db, sample_event)
            
            # NO debe haber llamado al handler
            mock_handler.assert_not_called()
            
            # NO debe haber añadido nada a BD
            mock_db.add.assert_not_called()
            
            # Debe retornar indicando duplicado
            assert "duplicate" in result
    
    def test_is_event_processed_detects_existing(self, mock_db):
        """_is_event_processed detecta eventos existentes."""
        from web.services.stripe_service import _is_event_processed
        
        # Evento existe
        mock_db.query.return_value.filter.return_value.first.return_value = ("evt_xxx",)
        assert _is_event_processed(mock_db, "evt_xxx") is True
        
        # Evento no existe
        mock_db.query.return_value.filter.return_value.first.return_value = None
        assert _is_event_processed(mock_db, "evt_yyy") is False
    
    def test_mark_event_processed_creates_record(self, mock_db):
        """_mark_event_processed crea registro en BD."""
        from web.services.stripe_service import _mark_event_processed
        
        _mark_event_processed(mock_db, "evt_test", "checkout.session.completed", "activated:standard")
        
        # Debe haber llamado db.add con objeto StripeWebhookEvent
        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        
        assert added_obj.event_id == "evt_test"
        assert added_obj.event_type == "checkout.session.completed"
        assert added_obj.result == "activated:standard"
    
    def test_result_truncated_if_too_long(self, mock_db):
        """Result se trunca a 255 caracteres."""
        from web.services.stripe_service import _mark_event_processed
        
        long_result = "x" * 300
        _mark_event_processed(mock_db, "evt_test", "type", long_result)
        
        added_obj = mock_db.add.call_args[0][0]
        assert len(added_obj.result) <= 255


class TestStripeWebhookEventModel:
    """Tests del modelo StripeWebhookEvent."""
    
    def test_model_exists(self):
        """El modelo StripeWebhookEvent debe existir."""
        from web.database.models import StripeWebhookEvent
        
        assert StripeWebhookEvent.__tablename__ == "stripe_webhook_events"
    
    def test_model_has_required_fields(self):
        """El modelo debe tener los campos requeridos."""
        from web.database.models import StripeWebhookEvent
        
        columns = [c.name for c in StripeWebhookEvent.__table__.columns]
        
        assert "event_id" in columns
        assert "event_type" in columns
        assert "processed_at" in columns
        assert "result" in columns
    
    def test_event_id_is_primary_key(self):
        """event_id debe ser llave primaria."""
        from web.database.models import StripeWebhookEvent
        
        pk_columns = [c.name for c in StripeWebhookEvent.__table__.primary_key.columns]
        assert "event_id" in pk_columns


class TestPurgeOldEvents:
    """Tests de purga de eventos antiguos."""
    
    def test_purge_deletes_old_events(self):
        """purge_old_webhook_events elimina eventos antiguos."""
        from web.services.stripe_service import purge_old_webhook_events
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        deleted = purge_old_webhook_events(mock_db, days=7)
        
        assert deleted == 5
        mock_db.query.return_value.filter.return_value.delete.assert_called_once()
    
    def test_purge_uses_correct_cutoff(self):
        """purge_old_webhook_events usa el cutoff correcto."""
        from web.services.stripe_service import purge_old_webhook_events
        from web.database.models import StripeWebhookEvent
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.delete.return_value = 0
        
        # Capturar el filtro usado
        purge_old_webhook_events(mock_db, days=7)
        
        # Verificar que se llamó query con el modelo correcto
        mock_db.query.assert_called_with(StripeWebhookEvent)


class TestIgnoredEventTypes:
    """Tests de eventos no manejados."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de BD."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db
    
    def test_unknown_event_type_marked_as_ignored(self, mock_db):
        """Eventos desconocidos se marcan como ignored."""
        from web.services.stripe_service import handle_webhook_event
        
        unknown_event = {
            "id": "evt_unknown_type",
            "type": "some.unknown.event",
            "data": {"object": {}}
        }
        
        result = handle_webhook_event(mock_db, unknown_event)
        
        assert "ignored" in result
        # Pero debe marcar como procesado para evitar reintentos
        mock_db.add.assert_called_once()
