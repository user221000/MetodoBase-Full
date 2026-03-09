"""
Tests para RotacionInteligenteAlimentos
========================================
Cubre los tres casos críticos del sistema de rotación con ventana deslizante.

Ejecutar con:
    python -m pytest tests/test_rotacion_inteligente.py -v
"""

import pytest
from src.gestor_rotacion import RotacionInteligenteAlimentos
from config.catalogo_alimentos import CATALOGO_POR_TIPO


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rotacion_vacia():
    """Instancia sin historial (cliente nuevo)."""
    r = RotacionInteligenteAlimentos.__new__(RotacionInteligenteAlimentos)
    r.id_cliente = "TEST_VACIO"
    r._archivo = "/dev/null"
    r.ventana_planes = 3
    r.historial = []
    r.frecuencias = {}
    return r


def _plan_simple(proteinas: list[str], carbs: list[str], grasas: list[str]) -> dict:
    """Construye un plan mínimo compatible con registrar_plan_nuevo."""
    alimentos: dict[str, float] = {}
    for ali in proteinas + carbs + grasas:
        alimentos[ali] = 150.0
    return {
        "comida": {
            "alimentos": alimentos
        }
    }


# ---------------------------------------------------------------------------
# TEST 1: Ventana deslizante — pesos correctos
# ---------------------------------------------------------------------------

class TestVentanaDeslizante:
    """Verifica que los pesos asignados correspondan a la distancia al plan actual."""

    def test_plan_inmediato_anterior_tiene_peso_1(self, rotacion_vacia):
        """Alimentos del plan n-1 deben recibir peso 1.0."""
        r = rotacion_vacia
        # Registrar un plan con pechuga
        r.historial = [
            {"proteina": ["pechuga_de_pollo"], "carbs": ["arroz_blanco"], "grasa": ["aguacate"]}
        ]
        r.frecuencias = r._calcular_frecuencias()

        pesos = r.obtener_penalizaciones_ponderadas()

        assert pesos.get("pechuga_de_pollo") == pytest.approx(1.0), (
            "El alimento del plan n-1 debe tener peso 1.0"
        )
        assert pesos.get("arroz_blanco") == pytest.approx(1.0)
        assert pesos.get("aguacate") == pytest.approx(1.0)

    def test_plan_dos_atras_tiene_peso_06(self, rotacion_vacia):
        """Alimentos del plan n-2 deben recibir peso 0.6."""
        r = rotacion_vacia
        r.historial = [
            {"proteina": ["salmon"], "carbs": ["papa"], "grasa": ["nueces"]},
            {"proteina": ["pechuga_de_pollo"], "carbs": ["arroz_blanco"], "grasa": ["aguacate"]},
        ]
        r.frecuencias = r._calcular_frecuencias()

        pesos = r.obtener_penalizaciones_ponderadas()

        # salmon fue usado en plan n-2 (índice 0, distancia 1 desde el final)
        assert pesos.get("salmon") == pytest.approx(0.6), (
            "Alimento de plan n-2 debe tener peso 0.6"
        )

    def test_plan_tres_atras_tiene_peso_03(self, rotacion_vacia):
        """Alimentos del plan n-3 deben recibir peso 0.3."""
        r = rotacion_vacia
        r.historial = [
            {"proteina": ["carne_magra_res"], "carbs": ["camote"], "grasa": ["almendras"]},
            {"proteina": ["salmon"], "carbs": ["papa"], "grasa": ["nueces"]},
            {"proteina": ["pechuga_de_pollo"], "carbs": ["arroz_blanco"], "grasa": ["aguacate"]},
        ]
        r.frecuencias = r._calcular_frecuencias()

        pesos = r.obtener_penalizaciones_ponderadas()

        assert pesos.get("carne_magra_res") == pytest.approx(0.3)
        assert pesos.get("camote") == pytest.approx(0.3)

    def test_alimentos_no_recientes_tienen_peso_cero(self, rotacion_vacia):
        """Alimentos no usados en los últimos 3 planes deben tener peso 0.0."""
        r = rotacion_vacia
        r.historial = [
            {"proteina": ["pechuga_de_pollo"], "carbs": [], "grasa": []},
        ]
        r.frecuencias = r._calcular_frecuencias()

        pesos = r.obtener_penalizaciones_ponderadas()

        # salmon no ha aparecido → no debe estar en el dict (peso implícito 0)
        assert pesos.get("salmon", 0.0) == pytest.approx(0.0)

    def test_ventana_no_excede_3_planes(self, rotacion_vacia):
        """Con 5 planes en historial, solo los 3 últimos influyen en los pesos."""
        r = rotacion_vacia
        r.ventana_planes = 3
        r.historial = [
            {"proteina": ["pescado_blanco"], "carbs": [], "grasa": []},  # n-5 — FUERA
            {"proteina": ["huevo"], "carbs": [], "grasa": []},            # n-4 — FUERA
            {"proteina": ["carne_magra_res"], "carbs": [], "grasa": []},  # n-3 — peso 0.3
            {"proteina": ["salmon"], "carbs": [], "grasa": []},           # n-2 — peso 0.6
            {"proteina": ["pechuga_de_pollo"], "carbs": [], "grasa": []}, # n-1 — peso 1.0
        ]
        r.frecuencias = r._calcular_frecuencias()

        pesos = r.obtener_penalizaciones_ponderadas()

        # Fuera de la ventana → peso 0
        assert pesos.get("pescado_blanco", 0.0) == pytest.approx(0.0)
        assert pesos.get("huevo", 0.0) == pytest.approx(0.0)
        # Dentro de la ventana
        assert pesos.get("carne_magra_res", 0.0) == pytest.approx(0.3)
        assert pesos.get("salmon", 0.0) == pytest.approx(0.6)
        assert pesos.get("pechuga_de_pollo", 0.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TEST 2: Alimentos infrautilizados
# ---------------------------------------------------------------------------

class TestSugerirInfraUtilizados:
    """Verifica que alimentos nunca usados aparecen primero en las sugerencias."""

    def test_nunca_usados_aparecen_primero(self, rotacion_vacia):
        """Un alimento con 0 usos debe salir antes que uno con 3 usos."""
        r = rotacion_vacia
        # Simular que 'pechuga_de_pollo' aparece 3 veces
        r.frecuencias = {"pechuga_de_pollo": 3, "salmon": 1}

        sugeridos = r.sugerir_alimentos_infrautilizados("proteina", top_n=3)

        # Los 3 primeros deben tener frecuencia 0 (no están en r.frecuencias)
        proteinas_con_cero = [
            p for p in CATALOGO_POR_TIPO["proteina"]
            if r.frecuencias.get(p, 0) == 0
        ]
        for ali in sugeridos:
            assert ali not in {"pechuga_de_pollo"}, (
                f"{ali} tiene alta frecuencia y no debería estar entre los primeros"
            )
        # Al menos uno debe ser de los que tienen frecuencia 0
        assert any(ali in proteinas_con_cero for ali in sugeridos), (
            "Debería sugerir alimentos con 0 usos antes que los más usados"
        )

    def test_top_n_respetado(self, rotacion_vacia):
        """El número de sugerencias no debe superar top_n."""
        r = rotacion_vacia
        r.frecuencias = {}

        for top in [1, 2, 5]:
            sugeridos = r.sugerir_alimentos_infrautilizados("proteina", top_n=top)
            assert len(sugeridos) <= top

    def test_categoria_invalida_devuelve_vacio(self, rotacion_vacia):
        """Una categoría inexistente debe devolver lista vacía, no excepción."""
        r = rotacion_vacia
        r.frecuencias = {}

        resultado = r.sugerir_alimentos_infrautilizados("no_existe", top_n=3)
        assert resultado == []

    def test_todos_los_alimentos_de_la_categoria_son_candidatos(self, rotacion_vacia):
        """Todos los alimentos del catálogo deben poder aparecer en sugerencias."""
        r = rotacion_vacia
        r.frecuencias = {}  # ninguno usado → todos tienen frecuencia 0

        sugeridos = r.sugerir_alimentos_infrautilizados("carbs", top_n=99)
        candidatos = set(CATALOGO_POR_TIPO["carbs"])

        for ali in sugeridos:
            assert ali in candidatos, f"{ali} no está en el catálogo de carbs"


# ---------------------------------------------------------------------------
# TEST 3: Balance de categorías (rotación equilibrada)
# ---------------------------------------------------------------------------

class TestBalanceCategorias:
    """Verifica que todas las categorías rotan equilibradamente a lo largo
    de múltiples planes simulados."""

    def _registrar_n_planes(self, r: RotacionInteligenteAlimentos, n: int) -> None:
        """Simula n registros usando proteínas distintas en orden."""
        proteinas = CATALOGO_POR_TIPO["proteina"]
        carbs = CATALOGO_POR_TIPO["carbs"]
        grasas = CATALOGO_POR_TIPO["grasa"]

        for i in range(n):
            plan = _plan_simple(
                proteinas=[proteinas[i % len(proteinas)]],
                carbs=[carbs[i % len(carbs)]],
                grasas=[grasas[i % len(grasas)]],
            )
            # Guardado en memoria (sin disco)
            r.historial.append({
                "proteina": [proteinas[i % len(proteinas)]],
                "carbs":    [carbs[i % len(carbs)]],
                "grasa":    [grasas[i % len(grasas)]],
            })
        r.frecuencias = r._calcular_frecuencias()

    def test_todas_las_categorias_tienen_frecuencia(self, rotacion_vacia):
        """Tras 7 planes, cada categoría debe tener al menos 1 alimento con
        frecuencia > 0."""
        r = rotacion_vacia
        self._registrar_n_planes(r, 7)

        for cat in ("proteina", "carbs", "grasa"):
            candidatos = CATALOGO_POR_TIPO[cat]
            al_menos_uno_usado = any(r.frecuencias.get(ali, 0) > 0 for ali in candidatos)
            assert al_menos_uno_usado, (
                f"La categoría '{cat}' no tiene ningún alimento con frecuencia > 0 "
                "tras 7 planes"
            )

    def test_rotacion_genera_variedad(self, rotacion_vacia):
        """Tras 7 planes con rotación ciclica, cada proteína usada debe
        aparecer un numero de veces razonable (no más de 2 para una ventana de 7
        si hay >= 4 proteínas disponibles)."""
        r = rotacion_vacia
        self._registrar_n_planes(r, 7)

        proteinas_usadas = {
            ali: count
            for ali, count in r.frecuencias.items()
            if ali in set(CATALOGO_POR_TIPO["proteina"])
        }
        # Con 9 proteínas en catálogo y 7 planes: ninguna debería aparecer más de 1
        for ali, count in proteinas_usadas.items():
            assert count <= 2, (
                f"{ali} aparece {count} veces en 7 planes — rotación desequilibrada"
            )

    def test_historial_se_limita_a_max(self, rotacion_vacia):
        """El historial no debe crecer más allá de MAX_HISTORIAL."""
        r = rotacion_vacia
        r._guardar_historial = lambda: None  # no escribir a disco
        self._registrar_n_planes(r, RotacionInteligenteAlimentos.MAX_HISTORIAL + 5)
        # Añadir manualmente al historial para llegar al límite
        while len(r.historial) < RotacionInteligenteAlimentos.MAX_HISTORIAL + 5:
            r.historial.append({"proteina": ["pechuga_de_pollo"], "carbs": [], "grasa": []})
        if len(r.historial) > RotacionInteligenteAlimentos.MAX_HISTORIAL:
            r.historial = r.historial[-RotacionInteligenteAlimentos.MAX_HISTORIAL:]
        assert len(r.historial) <= RotacionInteligenteAlimentos.MAX_HISTORIAL

    def test_penalizaciones_ponderadas_con_historial_vacio(self, rotacion_vacia):
        """Sin historial, obtener_penalizaciones_ponderadas debe devolver dict vacío."""
        r = rotacion_vacia
        pesos = r.obtener_penalizaciones_ponderadas()
        assert pesos == {}, "Sin historial debe devolver dict vacío"

    def test_como_penalizados_por_categoria_formato(self, rotacion_vacia):
        """como_penalizados_por_categoria debe devolver dict con 3 claves."""
        r = rotacion_vacia
        r.historial = [
            {"proteina": ["pechuga_de_pollo"], "carbs": ["arroz_blanco"], "grasa": ["aguacate"]}
        ]
        r.frecuencias = r._calcular_frecuencias()

        resultado = r.como_penalizados_por_categoria()

        assert set(resultado.keys()) == {"proteina", "carbs", "grasa"}
        assert "pechuga_de_pollo" in resultado["proteina"]
        assert "arroz_blanco" in resultado["carbs"]
        assert "aguacate" in resultado["grasa"]
