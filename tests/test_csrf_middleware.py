"""
tests/test_csrf_middleware.py — Tests para protección CSRF

Verifica:
- Tokens CSRF se generan correctamente
- Tokens firmados son válidos y expiran
- POST/PUT/DELETE requieren token válido
- GET/HEAD/OPTIONS están exentos
- Rutas con Bearer token están exentas
- Rutas específicas pueden eximirse
"""
import time
import pytest


class TestCSRFTokenGeneration:
    """Tests de generación y verificación de tokens."""
    
    def test_generate_token_format(self):
        """El token generado debe tener formato timestamp.random.signature."""
        from web.middleware.csrf import generate_csrf_token
        
        secret = "test_secret_key_at_least_32_chars"
        token = generate_csrf_token(secret)
        
        parts = token.split(".")
        assert len(parts) == 3, "Token debe tener 3 partes separadas por punto"
        
        timestamp, random_part, signature = parts
        assert timestamp.isdigit(), "Primera parte debe ser timestamp numérico"
        assert len(random_part) == 64, "Random debe ser 32 bytes en hex (64 chars)"
        assert len(signature) == 64, "Signature SHA256 debe ser 64 chars hex"
    
    def test_verify_token_valid(self):
        """Token recién generado debe ser válido."""
        from web.middleware.csrf import generate_csrf_token, verify_csrf_token
        
        secret = "test_secret_key_at_least_32_chars"
        token = generate_csrf_token(secret)
        
        assert verify_csrf_token(token, secret) is True
    
    def test_verify_token_wrong_secret(self):
        """Token con secret diferente no debe ser válido."""
        from web.middleware.csrf import generate_csrf_token, verify_csrf_token
        
        secret1 = "test_secret_key_at_least_32_chars"
        secret2 = "different_secret_key_32_chars_xx"
        
        token = generate_csrf_token(secret1)
        
        assert verify_csrf_token(token, secret2) is False
    
    def test_verify_token_tampered(self):
        """Token modificado no debe ser válido."""
        from web.middleware.csrf import generate_csrf_token, verify_csrf_token
        
        secret = "test_secret_key_at_least_32_chars"
        token = generate_csrf_token(secret)
        
        # Modificar la signature completamente (siempre cambia)
        parts = token.split(".")
        # Invertir la signature para garantizar que es diferente
        tampered_signature = parts[2][::-1]  # reverse string
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"
        
        assert verify_csrf_token(tampered_token, secret) is False
    
    def test_verify_token_expired(self):
        """Token expirado no debe ser válido."""
        from web.middleware.csrf import (
            _generate_token_raw,
            _sign_token,
            verify_csrf_token,
        )
        
        secret = "test_secret_key_at_least_32_chars"
        
        # Crear token con timestamp de hace 10 horas
        old_timestamp = int(time.time()) - (10 * 3600)
        raw_token = _generate_token_raw()
        expired_token = _sign_token(raw_token, secret, old_timestamp)
        
        # Con max_age default de 8 horas, debe estar expirado
        assert verify_csrf_token(expired_token, secret) is False
    
    def test_verify_token_empty(self):
        """Token vacío no debe ser válido."""
        from web.middleware.csrf import verify_csrf_token
        
        secret = "test_secret_key_at_least_32_chars"
        
        assert verify_csrf_token("", secret) is False
        assert verify_csrf_token(None, secret) is False
    
    def test_verify_token_malformed(self):
        """Token malformado no debe ser válido."""
        from web.middleware.csrf import verify_csrf_token
        
        secret = "test_secret_key_at_least_32_chars"
        
        # Menos de 3 partes
        assert verify_csrf_token("only.two", secret) is False
        # Timestamp no numérico
        assert verify_csrf_token("abc.random.signature", secret) is False


class TestCSRFMiddleware:
    """Tests del middleware integrado."""
    
    @pytest.fixture
    def csrf_client(self):
        """Cliente de test con CSRF middleware."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from web.middleware.csrf import CSRFMiddleware
        
        app = FastAPI()
        
        app.add_middleware(
            CSRFMiddleware,
            secret_key="test_secret_key_at_least_32_characters_long",
            exempt_paths=["/exempt/"],
            cookie_secure=False,
        )
        
        @app.get("/")
        async def root():
            return {"status": "ok"}
        
        @app.post("/submit")
        async def submit():
            return {"status": "submitted"}
        
        @app.put("/update")
        async def update():
            return {"status": "updated"}
        
        @app.delete("/delete")
        async def delete():
            return {"status": "deleted"}
        
        @app.post("/exempt/webhook")
        async def exempt_webhook():
            return {"status": "webhook"}
        
        return TestClient(app)
    
    def test_get_allowed_without_token(self, csrf_client):
        """GET debe funcionar sin token CSRF."""
        response = csrf_client.get("/")
        assert response.status_code == 200
    
    def test_get_sets_csrf_cookie(self, csrf_client):
        """GET debe establecer cookie CSRF."""
        response = csrf_client.get("/")
        assert "_csrf" in response.cookies
    
    def test_post_rejected_without_token(self, csrf_client):
        """POST sin token debe ser rechazado."""
        response = csrf_client.post("/submit")
        assert response.status_code == 403
        assert "missing" in response.json()["detail"].lower()
    
    def test_post_rejected_with_invalid_token(self, csrf_client):
        """POST con token inválido debe ser rechazado."""
        response = csrf_client.post(
            "/submit",
            headers={"X-CSRF-Token": "invalid.token.here"}
        )
        assert response.status_code == 403
        assert "invalid" in response.json()["detail"].lower()
    
    def test_post_allowed_with_valid_token(self, csrf_client):
        """POST con token válido debe funcionar."""
        # Primero obtener token con GET
        get_response = csrf_client.get("/")
        csrf_token = get_response.cookies.get("_csrf")
        
        # Usar token en POST
        response = csrf_client.post(
            "/submit",
            headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200
    
    def test_put_requires_token(self, csrf_client):
        """PUT también debe requerir token CSRF."""
        response = csrf_client.put("/update")
        assert response.status_code == 403
    
    def test_delete_requires_token(self, csrf_client):
        """DELETE también debe requerir token CSRF."""
        response = csrf_client.delete("/delete")
        assert response.status_code == 403
    
    def test_exempt_path_allowed_without_token(self, csrf_client):
        """Rutas exentas deben funcionar sin token."""
        response = csrf_client.post("/exempt/webhook")
        assert response.status_code == 200
    
    def test_bearer_token_exempts_csrf(self, csrf_client):
        """Requests con Bearer token deben estar exentas de CSRF."""
        response = csrf_client.post(
            "/submit",
            headers={"Authorization": "Bearer some_jwt_token"}
        )
        assert response.status_code == 200
    
    def test_form_token_also_accepted(self, csrf_client):
        """Token en campo de formulario debe ser aceptado."""
        # Obtener token
        get_response = csrf_client.get("/")
        csrf_token = get_response.cookies.get("_csrf")
        
        # Enviar como form field
        response = csrf_client.post(
            "/submit",
            data={"csrf_token": csrf_token}
        )
        assert response.status_code == 200


class TestCSRFMiddlewareConstruction:
    """Tests de construcción del middleware."""
    
    def test_requires_secret_key(self):
        """El middleware debe requerir secret_key."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from web.middleware.csrf import CSRFMiddleware
        
        app = FastAPI()
        app.add_middleware(CSRFMiddleware, secret_key="short")
        
        @app.get("/")
        async def root():
            return {"ok": True}
        
        # La validación ocurre cuando el middleware se instancia
        # al procesar la primera request
        with pytest.raises(ValueError, match="32 caracteres"):
            with TestClient(app):
                pass
    
    def test_accepts_valid_secret(self):
        """El middleware debe aceptar secret_key válida."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from web.middleware.csrf import CSRFMiddleware
        
        app = FastAPI()
        app.add_middleware(
            CSRFMiddleware,
            secret_key="this_is_a_valid_secret_key_32_chars_plus"
        )
        
        @app.get("/")
        async def root():
            return {"ok": True}
        
        # No debe lanzar excepción
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200


class TestCSRFHelpers:
    """Tests de funciones helper."""
    
    def test_get_csrf_token_from_request(self):
        """get_csrf_token debe obtener token de request.state."""
        from web.middleware.csrf import get_csrf_token
        from starlette.requests import Request
        from starlette.testclient import TestClient
        
        class MockState:
            csrf_token = "test_token_value"
        
        class MockRequest:
            state = MockState()
        
        token = get_csrf_token(MockRequest())
        assert token == "test_token_value"
    
    def test_csrf_input_html_format(self):
        """csrf_input_html debe generar HTML correcto."""
        from web.middleware.csrf import csrf_input_html
        
        class MockState:
            csrf_token = "abc123"
        
        class MockRequest:
            state = MockState()
        
        html = csrf_input_html(MockRequest())
        
        assert 'type="hidden"' in html
        assert 'name="csrf_token"' in html
        assert 'value="abc123"' in html
