"""
Tests para ValidadorCamposTiempoReal.
Verifica todas las reglas de validación de campos del formulario.

Ejecutar con:
    python -m pytest tests/test_validacion.py -v
"""

import pytest

# ValidadorCamposTiempoReal está en gui/app_gui.py pero no tiene dependencias
# de Tkinter (es una clase estática pura), por lo que se puede importar
# directamente sin inicializar la UI.
from gui.validadores import ValidadorCamposTiempoReal as V


# ---------------------------------------------------------------------------
# Peso
# ---------------------------------------------------------------------------

class TestValidarPeso:
    def test_peso_valido(self):
        ok, msg = V.validar_peso("75")
        assert ok is True
        assert msg == ""

    def test_peso_limite_inferior(self):
        ok, _ = V.validar_peso("20")
        assert ok is True

    def test_peso_limite_superior(self):
        ok, _ = V.validar_peso("155")
        assert ok is True

    def test_peso_muy_alto_rechazado(self):
        ok, msg = V.validar_peso("300")
        assert ok is False
        assert "155" in msg       # el mensaje menciona el límite máximo

    def test_peso_muy_bajo_rechazado(self):
        ok, msg = V.validar_peso("10")
        assert ok is False
        assert "20" in msg

    def test_peso_vacio(self):
        ok, _ = V.validar_peso("")
        assert ok is False

    def test_peso_no_numerico(self):
        ok, _ = V.validar_peso("abc")
        assert ok is False

    def test_peso_decimal(self):
        ok, _ = V.validar_peso("80.5")
        assert ok is True


# ---------------------------------------------------------------------------
# Nombre
# ---------------------------------------------------------------------------

class TestValidarNombre:
    def test_nombre_valido(self):
        ok, msg = V.validar_nombre("Oscar Hernández")
        assert ok is True
        assert msg == ""

    def test_nombre_vacio(self):
        ok, _ = V.validar_nombre("")
        assert ok is False

    def test_nombre_un_caracter(self):
        ok, _ = V.validar_nombre("A")
        assert ok is False

    def test_nombre_con_numeros(self):
        ok, msg = V.validar_nombre("Oscar1")
        assert ok is False
        assert "número" in msg.lower()


# ---------------------------------------------------------------------------
# Teléfono
# ---------------------------------------------------------------------------

class TestValidarTelefono:
    def test_telefono_vacio_es_valido(self):
        """El teléfono es opcional."""
        ok, _ = V.validar_telefono("")
        assert ok is True

    def test_telefono_valido(self):
        ok, _ = V.validar_telefono("5213312345678")
        assert ok is True

    def test_telefono_con_letras(self):
        ok, _ = V.validar_telefono("521abc1234")
        assert ok is False

    def test_telefono_muy_corto(self):
        ok, msg = V.validar_telefono("12345")
        assert ok is False
        assert "10" in msg


# ---------------------------------------------------------------------------
# Edad
# ---------------------------------------------------------------------------

class TestValidarEdad:
    def test_edad_valida(self):
        ok, _ = V.validar_edad("25")
        assert ok is True

    def test_edad_limite_inferior(self):
        ok, _ = V.validar_edad("10")
        assert ok is True

    def test_edad_limite_superior(self):
        ok, _ = V.validar_edad("100")
        assert ok is True

    def test_edad_menor_rango(self):
        ok, _ = V.validar_edad("5")
        assert ok is False

    def test_edad_mayor_rango(self):
        ok, _ = V.validar_edad("110")
        assert ok is False

    def test_edad_decimal(self):
        ok, _ = V.validar_edad("25.5")
        assert ok is False

    def test_edad_vacia(self):
        ok, _ = V.validar_edad("")
        assert ok is False


# ---------------------------------------------------------------------------
# Estatura
# ---------------------------------------------------------------------------

class TestValidarEstatura:
    def test_estatura_valida(self):
        ok, _ = V.validar_estatura("175")
        assert ok is True

    def test_estatura_muy_baja(self):
        ok, _ = V.validar_estatura("50")
        assert ok is False

    def test_estatura_muy_alta(self):
        ok, _ = V.validar_estatura("250")
        assert ok is False

    def test_estatura_limits(self):
        ok_min, _ = V.validar_estatura("100")
        ok_max, _ = V.validar_estatura("230")
        assert ok_min is True
        assert ok_max is True


# ---------------------------------------------------------------------------
# Grasa corporal
# ---------------------------------------------------------------------------

class TestValidarGrasa:
    def test_grasa_valida(self):
        ok, _ = V.validar_grasa("18")
        assert ok is True

    def test_grasa_minima(self):
        ok, _ = V.validar_grasa("5")
        assert ok is True

    def test_grasa_debajo_minimo(self):
        ok, msg = V.validar_grasa("3")
        assert ok is False
        assert "5" in msg

    def test_grasa_encima_maximo(self):
        ok, _ = V.validar_grasa("65")
        assert ok is False

    def test_grasa_vacia(self):
        ok, _ = V.validar_grasa("")
        assert ok is False
