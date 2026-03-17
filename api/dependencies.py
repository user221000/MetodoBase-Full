"""Dependency injection para MetodoBase API."""
import sys
import os
from pathlib import Path

# Asegurar que el root del proyecto está en sys.path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.gestor_bd import GestorBDClientes  # noqa: E402
from core.modelos import ClienteEvaluacion   # noqa: E402
from config.constantes import FACTORES_ACTIVIDAD  # noqa: E402

_gestor: GestorBDClientes | None = None


def get_gestor() -> GestorBDClientes:
    """Singleton: reutiliza una instancia de GestorBDClientes por proceso."""
    global _gestor
    if _gestor is None:
        db_path = os.getenv("DB_PATH", None)
        _gestor = GestorBDClientes(db_path=db_path)
    return _gestor


def build_cliente_from_dict(data: dict) -> ClienteEvaluacion:
    """
    Convierte un dict (de la API o de la BD) en ClienteEvaluacion con macros
    ya calculados via Katch-McArdle (MotorNutricional.calcular_motor).

    Si grasa_corporal_pct es None se asume 20% para que el motor no falle.
    """
    from core.motor_nutricional import MotorNutricional

    grasa = data.get("grasa_corporal_pct") or 20.0

    cliente = ClienteEvaluacion(
        nombre=data.get("nombre"),
        telefono=data.get("telefono"),
        edad=data.get("edad"),
        peso_kg=float(data.get("peso_kg") or 0),
        estatura_cm=float(data.get("estatura_cm") or 0),
        grasa_corporal_pct=float(grasa),
        nivel_actividad=data.get("nivel_actividad"),
        objetivo=data.get("objetivo"),
    )

    if data.get("id_cliente"):
        cliente.id_cliente = data["id_cliente"]

    cliente.factor_actividad = FACTORES_ACTIVIDAD.get(cliente.nivel_actividad or "", 1.2)
    cliente = MotorNutricional.calcular_motor(cliente)
    return cliente
