"""
Tests básicos de RotacionInteligenteAlimentos.
Complementa test_rotacion_inteligente.py con casos de caja negra de alto nivel.

Ejecutar con:
    python -m pytest tests/test_rotacion.py -v
"""

import os
import pytest

from src.gestor_rotacion import RotacionInteligenteAlimentos


# ---------------------------------------------------------------------------
# Fixture: instancia sin E/S a disco
# ---------------------------------------------------------------------------

@pytest.fixture
def gestor_limpio(tmp_path):
    """RotacionInteligenteAlimentos con directorio temporal, sin historial."""
    r = RotacionInteligenteAlimentos.__new__(RotacionInteligenteAlimentos)
    r.id_cliente = "TEST_ROT_001"
    r.ventana_planes = 3
    r._archivo = str(tmp_path / "rot.json")
    r.historial = []
    r.frecuencias = {}
    return r


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan(proteinas, carbs, grasas):
    """Construye un plan mínimo reconocible por registrar_plan_nuevo."""
    alimentos = {ali: 150.0 for ali in proteinas + carbs + grasas}
    return {"comida": {"alimentos": alimentos}}


# ---------------------------------------------------------------------------
# test_rotacion_basica
# ---------------------------------------------------------------------------

class TestRotacionBasica:
    def test_penalizacion_decrece_con_distancia(self, gestor_limpio):
        """El alimento más reciente debe tener mayor penalización que los anteriores."""
        r = gestor_limpio
        planes = [
            _plan(["huevo"],             ["avena"],          ["nueces"]),
            _plan(["pechuga_de_pollo"],   ["arroz_blanco"],   ["aguacate"]),
            _plan(["salmon"],            ["camote"],         ["aceite_de_oliva"]),
        ]
        for p in planes:
            r.registrar_plan_nuevo(p)

        pesos = r.obtener_penalizaciones_ponderadas()

        # salmon = plan n-1  →  peso 1.0
        # pechuga = plan n-2 →  peso 0.6
        # huevo   = plan n-3 →  peso 0.3
        assert pesos.get("salmon", 0) > pesos.get("pechuga_de_pollo", 0)
        assert pesos.get("pechuga_de_pollo", 0) > pesos.get("huevo", 0)

    def test_peso_plan_inmediato_es_1(self, gestor_limpio):
        """El plan n-1 debe recibir peso exactamente 1.0."""
        r = gestor_limpio
        r.registrar_plan_nuevo(_plan(["salmon"], ["camote"], ["aguacate"]))

        pesos = r.obtener_penalizaciones_ponderadas()

        assert pesos.get("salmon")  == pytest.approx(1.0)
        assert pesos.get("camote")  == pytest.approx(1.0)
        assert pesos.get("aguacate") == pytest.approx(1.0)

    def test_alimento_no_usado_tiene_peso_cero(self, gestor_limpio):
        """Un alimento que nunca apareció debe retornar peso 0."""
        r = gestor_limpio
        r.registrar_plan_nuevo(_plan(["pechuga_de_pollo"], ["arroz_blanco"], ["nueces"]))

        pesos = r.obtener_penalizaciones_ponderadas()

        # salmon no fue usado → no debe estar en el dict (o peso 0)
        assert pesos.get("salmon", 0.0) == pytest.approx(0.0)

    def test_historial_vacio_devuelve_dict_vacio(self, gestor_limpio):
        """Sin historial no hay penalizaciones."""
        pesos = gestor_limpio.obtener_penalizaciones_ponderadas()
        assert pesos == {}

    def test_max_historial_se_respeta(self, gestor_limpio):
        """El historial no debe crecer más allá de MAX_HISTORIAL."""
        r = gestor_limpio
        for i in range(RotacionInteligenteAlimentos.MAX_HISTORIAL + 5):
            r.registrar_plan_nuevo(_plan(["huevo"], ["papa"], ["nueces"]))

        assert len(r.historial) == RotacionInteligenteAlimentos.MAX_HISTORIAL


# ---------------------------------------------------------------------------
# test_sugerir_infrautilizados
# ---------------------------------------------------------------------------

class TestSugerirInfraUtilizados:
    def test_papa_sugerida_si_nunca_usada(self, gestor_limpio):
        """'papa' debe aparecer entre las sugerencias de carbs si nunca se usó."""
        r = gestor_limpio
        # Registrar planes sin papa
        for _ in range(3):
            r.registrar_plan_nuevo(_plan(
                ["pechuga_de_pollo"], ["arroz_blanco", "camote"], ["aguacate"]
            ))

        sugerencias = r.sugerir_alimentos_infrautilizados("carbs", top_n=5)

        assert "papa" in sugerencias

    def test_alimento_mas_usado_no_es_primero_en_sugerencias(self, gestor_limpio):
        """El alimento más repetido no debe encabezar las sugerencias."""
        r = gestor_limpio
        for _ in range(5):
            r.registrar_plan_nuevo(_plan(["huevo"], ["arroz_blanco"], ["nueces"]))

        sugerencias = r.sugerir_alimentos_infrautilizados("carbs", top_n=10)

        # arroz_blanco es el más usado, debe aparecer al final (o no en los top)
        if len(sugerencias) > 1:
            assert sugerencias[0] != "arroz_blanco"

    def test_categoria_invalida_retorna_lista_vacia(self, gestor_limpio):
        sugerencias = gestor_limpio.sugerir_alimentos_infrautilizados("INVALIDA", top_n=3)
        assert sugerencias == []

    def test_top_n_se_respeta(self, gestor_limpio):
        r = gestor_limpio
        r.registrar_plan_nuevo(_plan(["huevo"], ["avena"], ["nueces"]))
        sugerencias = r.sugerir_alimentos_infrautilizados("proteina", top_n=2)
        assert len(sugerencias) <= 2
