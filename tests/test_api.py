"""
Tests para la API REST — validación de schemas y lógica básica.

Ejecutar con:
    python -m pytest tests/test_api.py -v
"""
import pytest

# ── Schemas: PlanRequest ──────────────────────────────────────────────────────


def _import_pydantic():
    """Retorna True si pydantic está disponible, False si no."""
    try:
        import pydantic  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _import_pydantic(), reason="pydantic no instalado")
class TestPlanRequestSchema:
    """Valida que PlanRequest rechace entradas inválidas."""

    def _make_valid(self) -> dict:
        return {
            "nombre": "Ana García",
            "edad": 28,
            "peso_kg": 65.0,
            "estatura_cm": 165.0,
            "grasa_corporal_pct": 22.0,
            "nivel_actividad": "moderada",
            "objetivo": "deficit",
        }

    def test_request_valido(self):
        from api.schemas.planes import PlanRequest
        req = PlanRequest(**self._make_valid())
        assert req.nombre == "Ana García"
        assert req.objetivo == "deficit"

    def test_objetivo_normaliza_a_minusculas(self):
        from api.schemas.planes import PlanRequest
        data = self._make_valid()
        data["objetivo"] = "DEFICIT"
        req = PlanRequest(**data)
        assert req.objetivo == "deficit"

    def test_nivel_actividad_invalido_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.planes import PlanRequest
        data = self._make_valid()
        data["nivel_actividad"] = "extremo"
        with pytest.raises(ValidationError):
            PlanRequest(**data)

    def test_objetivo_invalido_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.planes import PlanRequest
        data = self._make_valid()
        data["objetivo"] = "volumen"
        with pytest.raises(ValidationError):
            PlanRequest(**data)

    def test_edad_fuera_de_rango_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.planes import PlanRequest
        data = self._make_valid()
        data["edad"] = 10
        with pytest.raises(ValidationError):
            PlanRequest(**data)

    def test_peso_fuera_de_rango_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.planes import PlanRequest
        data = self._make_valid()
        data["peso_kg"] = 5.0
        with pytest.raises(ValidationError):
            PlanRequest(**data)


# ── Schemas: RegistroRequest ──────────────────────────────────────────────────


@pytest.mark.skipif(not _import_pydantic(), reason="pydantic no instalado")
class TestRegistroRequestSchema:
    """Valida RegistroRequest."""

    def _make_valid(self) -> dict:
        return {
            "nombre": "Carlos",
            "apellido": "López",
            "email": "carlos@gym.com",
            "password": "Segura123!",
            "rol": "usuario",
        }

    def test_registro_valido(self):
        from api.schemas.auth import RegistroRequest
        req = RegistroRequest(**self._make_valid())
        assert req.email == "carlos@gym.com"

    def test_password_corta_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.auth import RegistroRequest
        data = self._make_valid()
        data["password"] = "abc"
        with pytest.raises(ValidationError):
            RegistroRequest(**data)

    def test_rol_invalido_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.auth import RegistroRequest
        data = self._make_valid()
        data["rol"] = "superusuario"
        with pytest.raises(ValidationError):
            RegistroRequest(**data)

    def test_email_invalido_lanza_error(self):
        from pydantic import ValidationError
        from api.schemas.auth import RegistroRequest
        data = self._make_valid()
        data["email"] = "no-es-email"
        with pytest.raises(ValidationError):
            RegistroRequest(**data)


# ── Cálculo nutricional en _CaloriasCard ─────────────────────────────────────

class TestCaloriasCalculo:
    """Prueba que _calcular_nutricional devuelve valores razonables."""

    def _mock_sesion(self):
        from unittest.mock import MagicMock
        sesion = MagicMock()
        sesion.nombre_display = "Test"
        sesion.rol = "usuario"
        return sesion

    def test_calculo_con_perfil_completo(self):
        from core.motor_nutricional import MotorNutricional
        from config.constantes import FACTORES_ACTIVIDAD

        perfil = {
            "peso_kg": 80.0,
            "grasa_corporal_pct": 20.0,
            "nivel_actividad": "moderada",
            "objetivo": "deficit",
        }
        factor = FACTORES_ACTIVIDAD.get(perfil["nivel_actividad"], 1.2)
        masa_magra = MotorNutricional.calcular_masa_magra(perfil["peso_kg"], perfil["grasa_corporal_pct"])
        tmb = MotorNutricional.calcular_tmb(masa_magra)
        get_total = MotorNutricional.calcular_get(tmb, factor)
        kcal_obj = MotorNutricional.calcular_kcal_objetivo(get_total, perfil["objetivo"])
        macros = MotorNutricional.calcular_macros(perfil["peso_kg"], kcal_obj)

        assert tmb > 1000
        assert get_total > tmb
        assert kcal_obj < get_total  # déficit
        assert macros["proteina_g"] == pytest.approx(80 * 1.8)
        assert macros["grasa_g"] == pytest.approx(80 * 0.8)
        assert macros["carbs_g"] > 0

    def test_calculo_superavit_mayor_que_get(self):
        from core.motor_nutricional import MotorNutricional
        from config.constantes import FACTORES_ACTIVIDAD

        peso, grasa = 75.0, 15.0
        factor = FACTORES_ACTIVIDAD["moderada"]
        masa_magra = MotorNutricional.calcular_masa_magra(peso, grasa)
        tmb = MotorNutricional.calcular_tmb(masa_magra)
        get_total = MotorNutricional.calcular_get(tmb, factor)
        kcal_superavit = MotorNutricional.calcular_kcal_objetivo(get_total, "superavit")

        assert kcal_superavit > get_total
