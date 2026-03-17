"""
tests/test_api.py — Smoke tests for MetodoBase FastAPI server.

Run with:
    source .venv/bin/activate
    pip install httpx pytest
    pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from api.app import create_app

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """One FastAPI TestClient reused across all tests in this module."""
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── /api/estadisticas ─────────────────────────────────────────────────────────

def test_estadisticas_returns_200(client):
    resp = client.get("/api/estadisticas")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_clientes" in data
    assert "clientes_activos" in data


# ── /api/clientes — list ──────────────────────────────────────────────────────

def test_listar_clientes_returns_200(client):
    resp = client.get("/api/clientes")
    assert resp.status_code == 200
    body = resp.json()
    assert "clientes" in body
    assert "total" in body
    assert isinstance(body["clientes"], list)


def test_listar_clientes_search(client):
    """Search query param should not crash even with no results."""
    resp = client.get("/api/clientes?q=zzz_nobody_zzz")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── /api/clientes — create (POST) ─────────────────────────────────────────────

VALID_CLIENTE = {
    "nombre": "Test Pytest",
    "edad": 30,
    "peso_kg": 70.0,
    "estatura_cm": 170.0,
    "grasa_corporal_pct": 15.0,
    "nivel_actividad": "moderada",
    "objetivo": "mantenimiento",
}


def test_crear_cliente_valido(client):
    resp = client.post("/api/clientes", json=VALID_CLIENTE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "id_cliente" in body
    assert body["macros"]["tmb"] > 0
    assert body["macros"]["proteina_g"] > 0
    # Store id for subsequent tests
    pytest.created_id = body["id_cliente"]


def test_crear_cliente_edad_invalida(client):
    bad = {**VALID_CLIENTE, "edad": 5}
    resp = client.post("/api/clientes", json=bad)
    assert resp.status_code == 422


def test_crear_cliente_peso_invalido(client):
    bad = {**VALID_CLIENTE, "peso_kg": 10.0}
    resp = client.post("/api/clientes", json=bad)
    assert resp.status_code == 422


def test_crear_cliente_nivel_invalido(client):
    bad = {**VALID_CLIENTE, "nivel_actividad": "super_intenso"}
    resp = client.post("/api/clientes", json=bad)
    assert resp.status_code == 422


def test_crear_cliente_objetivo_invalido(client):
    bad = {**VALID_CLIENTE, "objetivo": "bajar_peso"}
    resp = client.post("/api/clientes", json=bad)
    assert resp.status_code == 422


def test_crear_cliente_sin_grasa_usa_default(client):
    """grasa_corporal_pct is optional — should default to 20%."""
    sin_grasa = {k: v for k, v in VALID_CLIENTE.items() if k != "grasa_corporal_pct"}
    sin_grasa["nombre"] = "Sin Grasa"
    sin_grasa["edad"] = 25
    resp = client.post("/api/clientes", json=sin_grasa)
    assert resp.status_code == 201
    assert resp.json()["macros"]["tmb"] > 0


# ── /api/clientes/{id} — GET ──────────────────────────────────────────────────

def test_obtener_cliente_creado(client):
    if not hasattr(pytest, "created_id"):
        pytest.skip("Depends on test_crear_cliente_valido")
    resp = client.get(f"/api/clientes/{pytest.created_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id_cliente"] == pytest.created_id


def test_obtener_cliente_no_existente(client):
    resp = client.get("/api/clientes/ID_QUE_NO_EXISTE_ZZZZ")
    assert resp.status_code == 404


# ── /api/clientes/{id} — DELETE ──────────────────────────────────────────────

def test_soft_delete_cliente(client):
    if not hasattr(pytest, "created_id"):
        pytest.skip("Depends on test_crear_cliente_valido")
    resp = client.delete(f"/api/clientes/{pytest.created_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # Should now be hidden from default list
    resp2 = client.get(f"/api/clientes?q={pytest.created_id}")
    assert resp2.json()["total"] == 0


# ── HTML page routes ──────────────────────────────────────────────────────────

def test_dashboard_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"MetodoBase" in resp.content or b"dashboard" in resp.content.lower()


def test_nuevo_cliente_page(client):
    resp = client.get("/nuevo-cliente")
    assert resp.status_code == 200
    assert b"nuevo-cliente" in resp.content or b"step" in resp.content.lower()


def test_generar_plan_page(client):
    resp = client.get("/generar-plan/TESTID")
    assert resp.status_code == 200
    assert b"plan" in resp.content.lower()


# ── /docs ─────────────────────────────────────────────────────────────────────

def test_openapi_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


# ── /api/clientes/{id} — PUT (update) ────────────────────────────────────────

CLIENTE_PARA_ACTUALIZAR = {
    "nombre": "Cliente Actualizable",
    "edad": 28,
    "peso_kg": 75.0,
    "estatura_cm": 172.0,
    "grasa_corporal_pct": 16.0,
    "nivel_actividad": "leve",
    "objetivo": "mantenimiento",
}


def test_actualizar_cliente_peso(client):
    """PUT /api/clientes/{id} debe actualizar el peso correctamente."""
    # Crear cliente
    resp_create = client.post("/api/clientes", json=CLIENTE_PARA_ACTUALIZAR)
    assert resp_create.status_code == 201
    id_c = resp_create.json()["id_cliente"]

    # Actualizar peso
    resp_update = client.put(f"/api/clientes/{id_c}", json={"peso_kg": 72.5})
    assert resp_update.status_code == 200
    assert resp_update.json()["success"] is True

    # Verificar que el cambio persiste
    resp_get = client.get(f"/api/clientes/{id_c}")
    assert resp_get.status_code == 200
    assert float(resp_get.json()["peso_kg"]) == pytest.approx(72.5, abs=0.5)

    # Cleanup
    client.delete(f"/api/clientes/{id_c}")


def test_actualizar_cliente_objetivo(client):
    """PUT debe cambiar el objetivo del cliente."""
    resp_create = client.post("/api/clientes", json=CLIENTE_PARA_ACTUALIZAR)
    assert resp_create.status_code == 201
    id_c = resp_create.json()["id_cliente"]

    resp_update = client.put(f"/api/clientes/{id_c}", json={"objetivo": "deficit"})
    assert resp_update.status_code == 200

    # Verificar persistencia
    resp_get = client.get(f"/api/clientes/{id_c}")
    assert resp_get.json()["objetivo"] == "deficit"

    client.delete(f"/api/clientes/{id_c}")


def test_actualizar_cliente_no_existente_devuelve_404(client):
    """PUT con ID inválido debe retornar 404."""
    resp = client.put("/api/clientes/ID_NO_EXISTE_PUT_ZZZ", json={"peso_kg": 80.0})
    assert resp.status_code == 404


def test_actualizar_cliente_nivel_actividad(client):
    """PUT parcial solo actualiza los campos enviados."""
    resp_create = client.post("/api/clientes", json=CLIENTE_PARA_ACTUALIZAR)
    assert resp_create.status_code == 201
    id_c = resp_create.json()["id_cliente"]

    # Solo actualizar nivel de actividad
    resp_update = client.put(
        f"/api/clientes/{id_c}", json={"nivel_actividad": "intensa"}
    )
    assert resp_update.status_code == 200

    resp_get = client.get(f"/api/clientes/{id_c}")
    assert resp_get.json()["nivel_actividad"] == "intensa"
    # El nombre no debe haber cambiado
    assert "Actualizable" in resp_get.json()["nombre"]

    client.delete(f"/api/clientes/{id_c}")


# ── /api/descargar-pdf/{id_cliente} — descarga PDF real ─────────────────────

def test_descargar_pdf_despues_de_generar(client):
    """
    Flujo: crear cliente → generar plan → descargar PDF.
    Cubre la rama de FileResponse en routes/planes.py.
    """
    from pathlib import Path

    # Crear cliente
    resp_c = client.post("/api/clientes", json={
        "nombre": "Cliente Descarga PDF",
        "edad": 33,
        "peso_kg": 82.0,
        "estatura_cm": 176.0,
        "grasa_corporal_pct": 20.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
    })
    assert resp_c.status_code == 201
    id_c = resp_c.json()["id_cliente"]

    # Generar plan
    resp_plan = client.post("/api/generar-plan", json={
        "id_cliente": id_c, "plan_numero": 1
    })
    assert resp_plan.status_code == 200
    ruta_pdf = Path(resp_plan.json()["ruta_pdf"])

    # Descargar PDF
    resp_dl = client.get(f"/api/descargar-pdf/{id_c}")
    assert resp_dl.status_code == 200
    assert resp_dl.headers["content-type"] == "application/pdf"
    assert len(resp_dl.content) > 1024

    # Cleanup
    client.delete(f"/api/clientes/{id_c}")
    if ruta_pdf.exists():
        ruta_pdf.unlink(missing_ok=True)


def test_descargar_pdf_ruta_no_existente(client):
    """
    Si el registro BD apunta a un PDF borrado, debe retornar 404.
    Cubre la rama `not os.path.exists(ruta_pdf)` en planes.py.
    """
    import sqlite3
    from api.dependencies import get_gestor

    # Crear cliente y generar plan
    resp_c = client.post("/api/clientes", json={
        "nombre": "Cliente PDF Borrado",
        "edad": 29,
        "peso_kg": 68.0,
        "estatura_cm": 165.0,
        "nivel_actividad": "leve",
        "objetivo": "mantenimiento",
    })
    assert resp_c.status_code == 201
    id_c = resp_c.json()["id_cliente"]

    resp_plan = client.post("/api/generar-plan", json={"id_cliente": id_c, "plan_numero": 1})
    assert resp_plan.status_code == 200
    from pathlib import Path
    ruta_pdf = Path(resp_plan.json()["ruta_pdf"])

    # Borrar el PDF físico
    if ruta_pdf.exists():
        ruta_pdf.unlink()

    # Intentar descargar → 404
    resp_dl = client.get(f"/api/descargar-pdf/{id_c}")
    assert resp_dl.status_code == 404

    # Cleanup
    client.delete(f"/api/clientes/{id_c}")
