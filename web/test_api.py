"""
Tests básicos para la API REST de MetodoBase Web.

Ejecutar con:
    pytest web/test_api.py -v
"""
import sys
from pathlib import Path
import pytest

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from web.main_web import app

client = TestClient(app)


# ============================================================================
# TESTS DE HEALTH CHECK
# ============================================================================

def test_health_check():
    """El servidor responde con status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "MetodoBase Web" in data["app"]


# ============================================================================
# TESTS DE PÁGINAS HTML
# ============================================================================

def test_dashboard_carga():
    """El dashboard responde con HTML 200."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "MetodoBase" in resp.text


def test_clientes_pagina_carga():
    """La página de clientes responde con HTML 200."""
    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_generar_plan_pagina_carga():
    """La página de generar plan responde con HTML 200."""
    resp = client.get("/generar-plan")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


# ============================================================================
# TESTS DE ESTADÍSTICAS
# ============================================================================

def test_estadisticas_retorna_json():
    """El endpoint de estadísticas retorna JSON válido."""
    resp = client.get("/api/estadisticas")
    assert resp.status_code == 200
    data = resp.json()
    # Verificar campos esperados
    assert "total_clientes" in data
    assert "planes_periodo" in data
    assert "promedio_kcal" in data
    assert "clientes_activos" in data
    assert isinstance(data["total_clientes"], int)
    assert isinstance(data["promedio_kcal"], float)


# ============================================================================
# TESTS DE CLIENTES
# ============================================================================

def test_listar_clientes_retorna_lista():
    """El endpoint de listar clientes retorna una lista."""
    resp = client.get("/api/clientes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_listar_clientes_con_paginacion():
    """La paginación funciona correctamente."""
    resp = client.get("/api/clientes?pagina=1&por_pagina=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 5


def test_crear_cliente_valido():
    """Crear un cliente con datos válidos retorna 201."""
    payload = {
        "nombre": "Test Cliente API",
        "edad": 25,
        "peso_kg": 75.5,
        "estatura_cm": 175.0,
        "grasa_corporal_pct": 18.0,
        "nivel_actividad": "moderada",
        "objetivo": "mantenimiento",
    }
    resp = client.post("/api/clientes", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Test Cliente API"
    assert "id_cliente" in data
    assert data["edad"] == 25

    # Verificar que el cliente fue creado correctamente en la BD
    id_creado = data["id_cliente"]
    resp_get = client.get(f"/api/clientes/{id_creado}")
    assert resp_get.status_code == 200
    assert resp_get.json()["nombre"] == "Test Cliente API"


def test_crear_cliente_invalido_edad():
    """Crear cliente con edad inválida retorna error de validación."""
    payload = {
        "nombre": "Cliente Invalido",
        "edad": 5,  # Demasiado joven
        "peso_kg": 75.0,
        "estatura_cm": 170.0,
        "grasa_corporal_pct": 18.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
    }
    resp = client.post("/api/clientes", json=payload)
    assert resp.status_code == 422


def test_crear_cliente_invalido_objetivo():
    """Crear cliente con objetivo inválido retorna error de validación."""
    payload = {
        "nombre": "Cliente Invalido Obj",
        "edad": 25,
        "peso_kg": 75.0,
        "estatura_cm": 170.0,
        "grasa_corporal_pct": 18.0,
        "nivel_actividad": "moderada",
        "objetivo": "extremo",  # Objetivo no válido
    }
    resp = client.post("/api/clientes", json=payload)
    assert resp.status_code == 422


def test_obtener_cliente_no_existente():
    """Obtener cliente que no existe retorna 404."""
    resp = client.get("/api/clientes/ID_INEXISTENTE_XYZ")
    assert resp.status_code == 404


def test_buscar_clientes():
    """La búsqueda de clientes funciona."""
    resp = client.get("/api/clientes?buscar=Test&por_pagina=10")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ============================================================================
# TESTS DE PLANES
# ============================================================================

def test_generar_plan_cliente_inexistente():
    """Generar plan con cliente inexistente retorna 404."""
    payload = {
        "id_cliente": "ID_FALSO_XYZ",
        "peso_kg": 70.0,
        "grasa_corporal_pct": 20.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
    }
    resp = client.post("/api/generar-plan", json=payload)
    assert resp.status_code == 404


def test_descargar_pdf_no_existente():
    """Descargar PDF inexistente retorna 404."""
    resp = client.get("/api/descargar-pdf/archivo_inexistente.pdf")
    assert resp.status_code == 404


def test_descargar_pdf_path_traversal():
    """Prevenir ataques de path traversal en descarga de PDF."""
    resp = client.get("/api/descargar-pdf/../../../etc/passwd")
    assert resp.status_code in (400, 404)


def test_planes_cliente_inexistente():
    """Obtener planes de cliente inexistente retorna 404."""
    resp = client.get("/api/planes/ID_INEXISTENTE_XYZ")
    assert resp.status_code == 404
