"""
Tests para MotorNutricional.calcular_macros y calcular_motor.

Ejecutar con:
    python -m pytest tests/test_motor_nutricional.py -v
"""

import pytest
from core.motor_nutricional import MotorNutricional
from core.modelos import ClienteEvaluacion


# ---------------------------------------------------------------------------
# calcular_macros
# ---------------------------------------------------------------------------

class TestCalcularMacros:
    def test_proteina_es_18_por_kg(self):
        macros = MotorNutricional.calcular_macros(peso_kg=80, kcal_objetivo=2000)
        assert macros["proteina_g"] == pytest.approx(80 * 1.8)

    def test_grasa_es_08_por_kg(self):
        macros = MotorNutricional.calcular_macros(peso_kg=80, kcal_objetivo=2000)
        assert macros["grasa_g"] == pytest.approx(80 * 0.8)

    def test_carbs_positivos_con_calorias_suficientes(self):
        macros = MotorNutricional.calcular_macros(peso_kg=80, kcal_objetivo=2000)
        assert macros["carbs_g"] > 0

    def test_carbs_formula_residual(self):
        """carbs = (kcal - prot*4 - grasa*9) / 4."""
        peso, kcal = 70, 2200
        prot = 1.8 * peso
        grasa = 0.8 * peso
        carbs_esperado = (kcal - prot * 4 - grasa * 9) / 4
        macros = MotorNutricional.calcular_macros(peso_kg=peso, kcal_objetivo=kcal)
        assert macros["carbs_g"] == pytest.approx(carbs_esperado)

    def test_suma_kcal_aproximada(self):
        """Kcal proteína + grasa + carbs debe sumar cerca de kcal_objetivo."""
        macros = MotorNutricional.calcular_macros(peso_kg=75, kcal_objetivo=2100)
        total = (
            macros["proteina_g"] * 4
            + macros["grasa_g"] * 9
            + macros["carbs_g"] * 4
        )
        assert total == pytest.approx(2100, abs=1)

    def test_carbs_muy_bajos_dispara_alerta(self):
        """Con pocas kcal los carbs caen; debe generarse la alerta CARBS_MUY_BAJOS."""
        macros = MotorNutricional.calcular_macros(peso_kg=100, kcal_objetivo=1200)
        codigos = [a.codigo for a in macros.get("alertas", [])]
        assert "CARBS_MUY_BAJOS" in codigos

    def test_claves_requeridas_presentes(self):
        macros = MotorNutricional.calcular_macros(peso_kg=70, kcal_objetivo=2000)
        for clave in ("proteina_g", "grasa_g", "carbs_g", "alertas"):
            assert clave in macros

    def test_ajuste_grasa_cuando_carbs_negativos(self):
        """Si carbs resultan negativos, la grasa se reduce a 0.6 g/kg y carbs queda >= 0."""
        # peso=70, kcal=950: sin ajuste carbs=-14.5g; con ajuste grasa=42g → carbs=+17g
        macros = MotorNutricional.calcular_macros(peso_kg=70, kcal_objetivo=950)
        assert macros["carbs_g"] >= 0, "Los carbs deben ser >= 0 tras el ajuste de grasa"
        assert macros["grasa_g"] == 0.6 * 70, "La grasa debe reducirse a 0.6 g/kg"


# ---------------------------------------------------------------------------
# calcular_motor (integración)
# ---------------------------------------------------------------------------

class TestCalcularMotor:
    @pytest.fixture
    def cliente_base(self):
        c = ClienteEvaluacion(
            nombre="Test Cliente",
            edad=30,
            peso_kg=80,
            estatura_cm=175,
            grasa_corporal_pct=18,
            nivel_actividad="moderada",
            objetivo="mantenimiento",
        )
        c.factor_actividad = 1.55
        return c

    def test_tmb_es_positivo(self, cliente_base):
        c = MotorNutricional.calcular_motor(cliente_base)
        assert c.tmb > 0

    def test_get_mayor_que_tmb(self, cliente_base):
        c = MotorNutricional.calcular_motor(cliente_base)
        assert c.get_total > c.tmb

    def test_kcal_objetivo_asignada(self, cliente_base):
        c = MotorNutricional.calcular_motor(cliente_base)
        assert c.kcal_objetivo > 0

    def test_macros_asignados(self, cliente_base):
        c = MotorNutricional.calcular_motor(cliente_base)
        assert c.proteina_g > 0
        assert c.grasa_g > 0
        assert c.carbs_g > 0
