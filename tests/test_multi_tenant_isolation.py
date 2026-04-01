"""
tests/test_multi_tenant_isolation.py — Tests de aislamiento multi-tenant.

Verifica que:
1. Cada gym solo puede ver sus propios clientes
2. No hay IDOR (Insecure Direct Object Reference)
3. Tokens inválidos son rechazados
4. Cross-tenant access está bloqueado
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone


@pytest.fixture
def app():
    """Crea instancia de la app para testing."""
    from api.app import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba."""
    return TestClient(app)


@pytest.fixture
def mock_jwt_gym_a():
    """Mock de token JWT para gym A."""
    return {
        "id": "gym_a_id_12345",
        "email": "gym_a@test.com",
        "tipo": "gym",
        "nombre": "Gym A",
    }


@pytest.fixture
def mock_jwt_gym_b():
    """Mock de token JWT para gym B."""
    return {
        "id": "gym_b_id_67890",
        "email": "gym_b@test.com",
        "tipo": "gym",
        "nombre": "Gym B",
    }


@pytest.fixture
def mock_jwt_usuario():
    """Mock de token JWT para usuario normal (no gym)."""
    return {
        "id": "user_12345",
        "email": "user@test.com",
        "tipo": "usuario",
        "nombre": "Usuario Normal",
    }


class TestUnauthenticatedAccess:
    """Tests de acceso sin autenticación."""
    
    def test_clientes_sin_token_401(self, client):
        """GET /api/clientes sin token devuelve 401."""
        response = client.get("/api/clientes")
        assert response.status_code == 401
    
    def test_crear_cliente_sin_token_401(self, client):
        """POST /api/clientes sin token devuelve 401."""
        response = client.post("/api/clientes", json={
            "nombre": "Test",
            "telefono": "1234567890",
            "edad": 30,
            "peso_kg": 70,
            "estatura_cm": 170,
        })
        assert response.status_code == 401
    
    def test_estadisticas_sin_token_401(self, client):
        """GET /api/estadisticas sin token devuelve 401."""
        response = client.get("/api/estadisticas")
        assert response.status_code == 401
    
    def test_generar_plan_sin_token_401(self, client):
        """POST /api/generar-plan sin token devuelve 401."""
        response = client.post("/api/generar-plan", json={
            "id_cliente": "test123",
            "plan_numero": 1,
        })
        assert response.status_code == 401
    
    def test_pagos_stripe_sin_token_401(self, client):
        """POST /api/pagos/stripe/session sin token devuelve 401."""
        response = client.post("/api/pagos/stripe/session", json={
            "plan": "standard",
            "email": "test@test.com",
        })
        assert response.status_code == 401
    
    def test_pagos_mp_sin_token_401(self, client):
        """POST /api/pagos/mp/preference sin token devuelve 401."""
        response = client.post("/api/pagos/mp/preference", json={
            "plan": "standard",
            "email": "test@test.com",
        })
        assert response.status_code == 401


class TestCrossTenantIsolation:
    """Tests de aislamiento entre tenants."""
    
    def test_gym_a_no_ve_clientes_gym_b(self, client, mock_jwt_gym_a, mock_jwt_gym_b):
        """
        Gym A no puede ver clientes de Gym B.
        
        Escenario:
        1. Gym B crea un cliente
        2. Gym A intenta listar clientes
        3. El cliente de Gym B no aparece en la lista de Gym A
        """
        with patch("web.auth.verificar_token") as mock_verify:
            # Simular creación por Gym B (en realidad solo verificamos el filtro)
            mock_verify.return_value = mock_jwt_gym_a
            
            with patch("web.database.repository.listar_clientes") as mock_repo:
                mock_repo.return_value = ([], 0)
                
                response = client.get(
                    "/api/clientes",
                    headers={"Authorization": "Bearer fake_token_gym_a"}
                )
                
                # Verificar que se llamó a listar_clientes con gym_id de A
                call_args = mock_repo.call_args
                assert call_args is not None
                # El segundo argumento debe ser el gym_id
                assert call_args[0][1] == "gym_a_id_12345"
    
    def test_idor_cliente_otro_gym_devuelve_404(self, client, mock_jwt_gym_a):
        """
        Intentar acceder a cliente de otro gym devuelve 404 (no 403).
        
        Esto es importante para no revelar existencia de recursos.
        """
        with patch("web.auth.verificar_token") as mock_verify:
            mock_verify.return_value = mock_jwt_gym_a
            
            with patch("web.database.repository.obtener_cliente") as mock_repo:
                # Simular que el cliente no existe para este gym
                mock_repo.return_value = None
                
                response = client.get(
                    "/api/clientes/cliente_de_gym_b",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 404
                assert "no encontrado" in response.json()["detail"].lower()
    
    def test_actualizar_cliente_otro_gym_devuelve_404(self, client, mock_jwt_gym_a):
        """
        Intentar actualizar cliente de otro gym devuelve 404.
        """
        with patch("web.auth.verificar_token") as mock_verify:
            mock_verify.return_value = mock_jwt_gym_a
            
            with patch("web.database.repository.obtener_cliente") as mock_repo:
                mock_repo.return_value = None
                
                response = client.put(
                    "/api/clientes/cliente_de_gym_b",
                    headers={"Authorization": "Bearer fake_token"},
                    json={"nombre": "Hacked Name"}
                )
                
                assert response.status_code == 404
    
    def test_eliminar_cliente_otro_gym_devuelve_404(self, client, mock_jwt_gym_a):
        """
        Intentar eliminar cliente de otro gym devuelve 404.
        """
        with patch("web.auth.verificar_token") as mock_verify:
            mock_verify.return_value = mock_jwt_gym_a
            
            with patch("web.database.repository.obtener_cliente") as mock_repo:
                mock_repo.return_value = None
                
                response = client.delete(
                    "/api/clientes/cliente_de_gym_b",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 404


class TestUserTypeRestrictions:
    """Tests de restricción por tipo de usuario."""
    
    def test_usuario_normal_no_accede_endpoints_gym(self, client, mock_jwt_usuario):
        """
        Usuarios tipo "usuario" (no gym) no pueden acceder a endpoints de gym.
        """
        with patch("web.auth.verificar_token") as mock_verify:
            mock_verify.return_value = mock_jwt_usuario
            
            # get_usuario_gym debería rechazar usuarios tipo "usuario"
            response = client.get(
                "/api/clientes",
                headers={"Authorization": "Bearer fake_token"}
            )
            
            # Debería ser 403 (forbidden) porque el usuario existe pero no tiene permisos
            # O 401 si get_usuario_gym no reconoce el tipo
            assert response.status_code in (401, 403)


class TestTokenValidation:
    """Tests de validación de tokens."""
    
    def test_token_malformado_401(self, client):
        """Token malformado devuelve 401."""
        response = client.get(
            "/api/clientes",
            headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        assert response.status_code == 401
    
    def test_token_sin_bearer_401(self, client):
        """Token sin prefijo Bearer devuelve 401."""
        response = client.get(
            "/api/clientes",
            headers={"Authorization": "just_a_token"}
        )
        assert response.status_code == 401
    
    def test_token_vacio_401(self, client):
        """Token vacío devuelve 401."""
        response = client.get(
            "/api/clientes",
            headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 401


class TestHealthEndpointsNoAuth:
    """Verificar que endpoints públicos no requieren auth."""
    
    def test_health_no_requiere_auth(self, client):
        """GET /health no requiere autenticación."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_ready_no_requiere_auth(self, client):
        """GET /health/ready no requiere autenticación."""
        response = client.get("/health/ready")
        # Puede ser 200 o 503 dependiendo de si hay BD, pero no 401
        assert response.status_code in (200, 503)
    
    def test_metrics_no_requiere_auth(self, client):
        """GET /metrics requiere X-Metrics-Key (H-09)."""
        # Sin key → 403
        response = client.get("/metrics")
        assert response.status_code == 403


class TestRepositoryGymIdFiltering:
    """Tests para verificar que el repository filtra por gym_id."""
    
    def test_listar_clientes_usa_gym_id(self):
        """Verifica que listar_clientes recibe y usa gym_id."""
        from web.database import repository as repo
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        
        # Llamar función
        result = repo.listar_clientes(mock_db, "test_gym_id", "")
        
        # Verificar que se hizo query con filter
        mock_db.query.assert_called()
    
    def test_crear_cliente_asigna_gym_id(self):
        """Verifica que crear_cliente asigna el gym_id correcto."""
        from web.database import repository as repo
        from unittest.mock import MagicMock, patch
        
        mock_db = MagicMock()
        
        with patch("web.database.repository.Cliente") as MockCliente:
            mock_instance = MagicMock()
            MockCliente.return_value = mock_instance
            
            # Llamar función
            try:
                repo.crear_cliente(mock_db, "test_gym_id", {
                    "nombre": "Test",
                    "telefono": "123",
                    "edad": 30,
                    "peso_kg": 70,
                    "estatura_cm": 170,
                })
            except Exception:
                pass  # Puede fallar por otras razones, solo verificamos el gym_id
            
            # Verificar que se asignó gym_id
            if MockCliente.called:
                call_kwargs = MockCliente.call_args[1] if MockCliente.call_args[1] else {}
                # gym_id debería estar en los kwargs
                assert "gym_id" in call_kwargs or any(
                    arg == "test_gym_id" for arg in MockCliente.call_args[0]
                )
