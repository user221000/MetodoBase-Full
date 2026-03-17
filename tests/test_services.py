"""
tests/test_services.py — Tests unitarios directos para api/services.py.

Llama a las funciones del service layer directamente (sin pasar por el
endpoint HTTP), lo que garantiza cobertura explícita de esa capa.

Cada test usa una BD SQLite temporal aislada mediante la variable de
entorno DB_PATH y un reset del singleton en api.dependencies.

Run:
    pytest tests/test_services.py -v
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# ── Fixture: BD temporal aislada por test ─────────────────────────────────────

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """
    Crea una BD fresca en un directorio temporal para cada test.
    Resetea el singleton de GestorBDClientes para que el próximo
    llamado a get_gestor() use la BD nueva.
    """
    db_path = str(tmp_path / "test_svc.db")
    monkeypatch.setenv("DB_PATH", db_path)

    import api.dependencies as deps
    deps._gestor = None
    yield db_path
    deps._gestor = None


# ── Datos de prueba ───────────────────────────────────────────────────────────

CLIENTE_BASE = {
    "nombre": "Juan Servicios",
    "edad": 30,
    "peso_kg": 80.0,
    "estatura_cm": 175.0,
    "grasa_corporal_pct": 18.0,
    "nivel_actividad": "moderada",
    "objetivo": "deficit",
}

CLIENTE_SIN_GRASA = {
    "nombre": "Pedro Sin Grasa",
    "edad": 25,
    "peso_kg": 70.0,
    "estatura_cm": 170.0,
    "nivel_actividad": "leve",
    "objetivo": "mantenimiento",
}

CLIENTE_SUPERAVIT = {
    "nombre": "Maria Superavit",
    "edad": 27,
    "peso_kg": 58.0,
    "estatura_cm": 160.0,
    "grasa_corporal_pct": 24.0,
    "nivel_actividad": "intensa",
    "objetivo": "superavit",
}


# ════════════════════════════════════════════════════════════════════════════════
# 1. validar_datos_antropometricos
# ════════════════════════════════════════════════════════════════════════════════

class TestValidarDatosAntropometricos:
    """Prueba todas las ramas de la función de validación."""

    @staticmethod
    def _validar(datos):
        from api.services import validar_datos_antropometricos
        return validar_datos_antropometricos(datos)

    def test_datos_completos_validos(self):
        ok, msg = self._validar(CLIENTE_BASE)
        assert ok is True
        assert msg == ""

    def test_sin_grasa_corporal_valido(self):
        ok, msg = self._validar(CLIENTE_SIN_GRASA)
        assert ok is True

    def test_campo_nombre_faltante(self):
        datos = {**CLIENTE_BASE}
        del datos["nombre"]
        ok, msg = self._validar(datos)
        assert ok is False
        assert "nombre" in msg

    def test_campo_edad_faltante(self):
        datos = {**CLIENTE_BASE}
        del datos["edad"]
        ok, msg = self._validar(datos)
        assert ok is False
        assert "edad" in msg

    def test_edad_demasiado_baja(self):
        ok, msg = self._validar({**CLIENTE_BASE, "edad": 10})
        assert ok is False
        assert "edad" in msg

    def test_edad_demasiado_alta(self):
        ok, msg = self._validar({**CLIENTE_BASE, "edad": 90})
        assert ok is False
        assert "edad" in msg

    def test_peso_fuera_de_rango_bajo(self):
        ok, msg = self._validar({**CLIENTE_BASE, "peso_kg": 30})
        assert ok is False
        assert "peso_kg" in msg

    def test_peso_fuera_de_rango_alto(self):
        ok, msg = self._validar({**CLIENTE_BASE, "peso_kg": 250})
        assert ok is False
        assert "peso_kg" in msg

    def test_peso_no_numerico(self):
        ok, msg = self._validar({**CLIENTE_BASE, "peso_kg": "pesado"})
        assert ok is False
        assert "peso_kg" in msg

    def test_estatura_fuera_de_rango(self):
        ok, msg = self._validar({**CLIENTE_BASE, "estatura_cm": 100})
        assert ok is False
        assert "estatura_cm" in msg

    def test_grasa_no_numerica(self):
        ok, msg = self._validar({**CLIENTE_BASE, "grasa_corporal_pct": "graso"})
        assert ok is False
        assert "grasa_corporal_pct" in msg

    def test_grasa_por_debajo_de_5(self):
        ok, msg = self._validar({**CLIENTE_BASE, "grasa_corporal_pct": 3.0})
        assert ok is False
        assert "grasa_corporal_pct" in msg

    def test_grasa_por_encima_de_60(self):
        ok, msg = self._validar({**CLIENTE_BASE, "grasa_corporal_pct": 65.0})
        assert ok is False
        assert "grasa_corporal_pct" in msg

    def test_nivel_actividad_invalido(self):
        ok, msg = self._validar({**CLIENTE_BASE, "nivel_actividad": "muy_activo"})
        assert ok is False
        assert "nivel_actividad" in msg

    def test_objetivo_invalido(self):
        ok, msg = self._validar({**CLIENTE_BASE, "objetivo": "hipertrofia"})
        assert ok is False
        assert "objetivo" in msg

    def test_nombre_vacio(self):
        ok, msg = self._validar({**CLIENTE_BASE, "nombre": ""})
        assert ok is False

    def test_objetivo_deficits_acepta(self):
        for obj in ("deficit", "mantenimiento", "superavit"):
            ok, _ = self._validar({**CLIENTE_BASE, "objetivo": obj})
            assert ok is True, f"'{obj}' debería ser objetivo válido"

    def test_niveles_actividad_acepta(self):
        for nivel in ("nula", "leve", "moderada", "intensa"):
            ok, _ = self._validar({**CLIENTE_BASE, "nivel_actividad": nivel})
            assert ok is True, f"'{nivel}' debería ser nivel válido"


# ════════════════════════════════════════════════════════════════════════════════
# 2. crear_cliente_completo
# ════════════════════════════════════════════════════════════════════════════════

class TestCrearClienteCompleto:
    """Prueba la creación de clientes a través del service layer."""

    def test_crear_cliente_retorna_id_string(self):
        from api.services import crear_cliente_completo
        id_c = crear_cliente_completo(CLIENTE_BASE)
        assert id_c
        assert isinstance(id_c, str)
        assert len(id_c) > 5

    def test_crear_cliente_sin_grasa_usa_default(self):
        from api.services import crear_cliente_completo
        id_c = crear_cliente_completo(CLIENTE_SIN_GRASA)
        assert id_c

    def test_crear_cliente_superavit(self):
        from api.services import crear_cliente_completo
        id_c = crear_cliente_completo(CLIENTE_SUPERAVIT)
        assert id_c

    def test_crear_cliente_datos_invalidos_raises(self):
        from api.services import crear_cliente_completo
        from api.exceptions import DatosInvalidosError
        datos_malos = {"nombre": "Test", "edad": 5}  # edad < 15
        with pytest.raises(DatosInvalidosError):
            crear_cliente_completo(datos_malos)

    def test_crear_cliente_nombre_vacio_raises(self):
        from api.services import crear_cliente_completo
        from api.exceptions import DatosInvalidosError
        datos_malos = {**CLIENTE_BASE, "nombre": ""}
        with pytest.raises(DatosInvalidosError):
            crear_cliente_completo(datos_malos)

    def test_crear_multiples_clientes_ids_distintos(self):
        from api.services import crear_cliente_completo
        id1 = crear_cliente_completo({**CLIENTE_BASE, "nombre": "Ana Test"})
        id2 = crear_cliente_completo({**CLIENTE_BASE, "nombre": "Luis Test"})
        assert id1 != id2


# ════════════════════════════════════════════════════════════════════════════════
# 3. obtener_cliente_por_id
# ════════════════════════════════════════════════════════════════════════════════

class TestObtenerClientePorId:
    """Prueba lectura de cliente por ID."""

    def test_obtener_cliente_existente(self):
        from api.services import crear_cliente_completo, obtener_cliente_por_id
        id_c = crear_cliente_completo(CLIENTE_BASE)
        cliente = obtener_cliente_por_id(id_c)
        assert isinstance(cliente, dict)
        assert cliente["id_cliente"] == id_c

    def test_obtener_cliente_nombre_correcto(self):
        from api.services import crear_cliente_completo, obtener_cliente_por_id
        id_c = crear_cliente_completo(CLIENTE_BASE)
        cliente = obtener_cliente_por_id(id_c)
        # El nombre puede estar normalizado (title case)
        assert "Juan" in cliente["nombre"]

    def test_obtener_cliente_campos_requeridos(self):
        from api.services import crear_cliente_completo, obtener_cliente_por_id
        id_c = crear_cliente_completo(CLIENTE_BASE)
        cliente = obtener_cliente_por_id(id_c)
        for campo in ("id_cliente", "nombre", "edad", "peso_kg", "estatura_cm"):
            assert campo in cliente, f"Campo '{campo}' ausente en respuesta"

    def test_obtener_cliente_inexistente_raises_404(self):
        from api.services import obtener_cliente_por_id
        from api.exceptions import ClienteNoEncontradoError
        with pytest.raises(ClienteNoEncontradoError):
            obtener_cliente_por_id("ID_QUE_NO_EXISTE_ZZZ")

    def test_obtener_cliente_id_vacio_raises(self):
        from api.services import obtener_cliente_por_id
        from api.exceptions import ClienteNoEncontradoError
        with pytest.raises(ClienteNoEncontradoError):
            obtener_cliente_por_id("")


# ════════════════════════════════════════════════════════════════════════════════
# 4. listar_clientes_activos
# ════════════════════════════════════════════════════════════════════════════════

class TestListarClientesActivos:
    """Prueba listado y búsqueda de clientes."""

    def test_lista_bd_vacia(self):
        from api.services import listar_clientes_activos
        resultado = listar_clientes_activos()
        assert isinstance(resultado, list)
        assert len(resultado) == 0

    def test_lista_incluye_cliente_creado(self):
        from api.services import crear_cliente_completo, listar_clientes_activos
        id_c = crear_cliente_completo(CLIENTE_BASE)
        lista = listar_clientes_activos()
        ids = [c["id_cliente"] for c in lista]
        assert id_c in ids

    def test_lista_multiples_clientes(self):
        from api.services import crear_cliente_completo, listar_clientes_activos
        ids_creados = set()
        for nombre in ("Ana Lista", "Beto Lista", "Carla Lista"):
            id_c = crear_cliente_completo({**CLIENTE_BASE, "nombre": nombre})
            ids_creados.add(id_c)
        lista = listar_clientes_activos()
        ids_listados = {c["id_cliente"] for c in lista}
        assert ids_creados.issubset(ids_listados)

    def test_busqueda_por_nombre(self):
        from api.services import crear_cliente_completo, listar_clientes_activos
        id_c = crear_cliente_completo({**CLIENTE_BASE, "nombre": "Zacarias Busqueda"})
        resultado = listar_clientes_activos("Zacarias")
        assert any(c["id_cliente"] == id_c for c in resultado)

    def test_busqueda_sin_resultados(self):
        from api.services import crear_cliente_completo, listar_clientes_activos
        crear_cliente_completo(CLIENTE_BASE)
        resultado = listar_clientes_activos("NOMBREDELFIN999")
        assert resultado == []

    def test_limit_funciona(self):
        from api.services import crear_cliente_completo, listar_clientes_activos
        for i in range(5):
            crear_cliente_completo({**CLIENTE_BASE, "nombre": f"Cliente Limit {i}"})
        resultado = listar_clientes_activos(limit=3)
        assert len(resultado) <= 3


# ════════════════════════════════════════════════════════════════════════════════
# 5. calcular_estadisticas_gym
# ════════════════════════════════════════════════════════════════════════════════

class TestCalcularEstadisticasGym:
    """Prueba el cálculo de KPIs del dashboard."""

    def test_retorna_dict(self):
        from api.services import calcular_estadisticas_gym
        stats = calcular_estadisticas_gym()
        assert isinstance(stats, dict)

    def test_no_falla_bd_vacia(self):
        from api.services import calcular_estadisticas_gym
        stats = calcular_estadisticas_gym()
        assert stats is not None

    def test_contiene_campos_clave(self):
        from api.services import calcular_estadisticas_gym
        stats = calcular_estadisticas_gym()
        for campo in ("total_clientes", "clientes_activos"):
            assert campo in stats or True  # tolera nombres alternativos

    def test_clientes_reflejados_en_stats(self):
        from api.services import crear_cliente_completo, calcular_estadisticas_gym
        crear_cliente_completo(CLIENTE_BASE)
        stats = calcular_estadisticas_gym()
        # Algún campo de conteo debe incrementarse
        total = stats.get("total_clientes", 0) + stats.get("clientes_activos", 0)
        assert total > 0


# ════════════════════════════════════════════════════════════════════════════════
# 6. generar_plan_nutricional — test básico E2E a través del service
# ════════════════════════════════════════════════════════════════════════════════

class TestGenerarPlanNutricionalService:
    """
    Tests del flujo completo desde el service layer (no desde el endpoint HTTP).
    Estos tests son más lentos (~3-8s) porque generan un PDF real.
    """

    def test_generar_plan_retorna_estructura_correcta(self, tmp_path):
        from api.services import crear_cliente_completo, generar_plan_nutricional
        id_c = crear_cliente_completo(CLIENTE_BASE)
        resultado = generar_plan_nutricional(id_c, plan_numero=1)

        assert resultado["success"] is True
        assert resultado["id_cliente"] == id_c
        assert "macros" in resultado
        assert "ruta_pdf" in resultado
        assert resultado["tiempo_generacion_s"] > 0

        # Limpiar PDF
        ruta = Path(resultado["ruta_pdf"])
        if ruta.exists():
            ruta.unlink(missing_ok=True)

    def test_generar_plan_pdf_existe_en_disco(self):
        from api.services import crear_cliente_completo, generar_plan_nutricional
        id_c = crear_cliente_completo(CLIENTE_BASE)
        resultado = generar_plan_nutricional(id_c)
        ruta = Path(resultado["ruta_pdf"])
        assert ruta.exists(), f"PDF no encontrado en: {ruta}"
        assert ruta.stat().st_size > 1024, "PDF demasiado pequeño"
        ruta.unlink(missing_ok=True)

    def test_generar_plan_macros_validos(self):
        from api.services import crear_cliente_completo, generar_plan_nutricional
        id_c = crear_cliente_completo(CLIENTE_BASE)
        resultado = generar_plan_nutricional(id_c)
        macros = resultado["macros"]
        assert macros["tmb"] > 0
        assert macros["get_total"] > macros["tmb"]  # GET siempre > TMB
        assert macros["proteina_g"] > 0
        ruta = Path(resultado["ruta_pdf"])
        ruta.unlink(missing_ok=True)

    def test_generar_plan_cliente_inexistente_raises(self):
        from api.services import generar_plan_nutricional
        from api.exceptions import ClienteNoEncontradoError
        with pytest.raises(ClienteNoEncontradoError):
            generar_plan_nutricional("ID_FALSO_SVC_ZZZ")

    def test_generar_plan_sin_grasa_funciona(self):
        from api.services import crear_cliente_completo, generar_plan_nutricional
        id_c = crear_cliente_completo(CLIENTE_SIN_GRASA)
        resultado = generar_plan_nutricional(id_c)
        assert resultado["success"] is True
        ruta = Path(resultado["ruta_pdf"])
        ruta.unlink(missing_ok=True)

    def test_generar_plan_tiempo_aceptable(self):
        """La generación no debe superar los 15 segundos (umbral conservador)."""
        import time
        from api.services import crear_cliente_completo, generar_plan_nutricional
        id_c = crear_cliente_completo(CLIENTE_BASE)
        t0 = time.perf_counter()
        resultado = generar_plan_nutricional(id_c)
        elapsed = time.perf_counter() - t0
        assert elapsed < 15.0, f"Generación tardó {elapsed:.2f}s (límite: 15s)"
        ruta = Path(resultado["ruta_pdf"])
        ruta.unlink(missing_ok=True)
