# -*- coding: utf-8 -*-
"""Reglas de validación de campos del formulario — sin dependencias de Tkinter."""

# ── Canonical validation ranges (single source of truth) ─────────────────────
RANGO_EDAD = (10, 100)
RANGO_PESO = (20, 300)
RANGO_ESTATURA = (100, 250)
RANGO_GRASA = (3, 60)


class ValidadorCamposTiempoReal:
    """Reglas de validación sin acoplamiento a widgets de Tkinter."""

    @staticmethod
    def validar_nombre(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if not v:
            return False, "El nombre es obligatorio"
        if len(v) < 2:
            return False, "Mínimo 2 caracteres"
        if any(ch.isdigit() for ch in v):
            return False, "El nombre no debe contener números"
        return True, ""

    @staticmethod
    def validar_telefono(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if v == "":
            return True, ""          # opcional
        if not v.isdigit():
            return False, "Solo números, sin espacios"
        if len(v) < 10:
            return False, "Mínimo 10 dígitos"
        return True, ""

    @staticmethod
    def validar_edad(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if not v:
            return False, "Campo obligatorio"
        try:
            edad = int(v)
        except ValueError:
            return False, "Debe ser un número entero"
        if edad < RANGO_EDAD[0] or edad > RANGO_EDAD[1]:
            return False, f"Edad fuera de rango ({RANGO_EDAD[0]}–{RANGO_EDAD[1]})"
        return True, ""

    @staticmethod
    def validar_peso(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if not v:
            return False, "Campo obligatorio"
        try:
            peso = float(v)
        except ValueError:
            return False, "Debe ser un número"
        if peso < RANGO_PESO[0]:
            return False, f"Mínimo {RANGO_PESO[0]} kg"
        if peso > RANGO_PESO[1]:
            return False, f"Máximo {RANGO_PESO[1]} kg"
        return True, ""

    @staticmethod
    def validar_estatura(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if not v:
            return False, "Campo obligatorio"
        try:
            est = float(v)
        except ValueError:
            return False, "Debe ser un número"
        if est < RANGO_ESTATURA[0] or est > RANGO_ESTATURA[1]:
            return False, f"Rango válido: {RANGO_ESTATURA[0]}–{RANGO_ESTATURA[1]} cm"
        return True, ""

    @staticmethod
    def validar_grasa(valor: str) -> tuple[bool, str]:
        v = valor.strip()
        if not v:
            return False, "Campo obligatorio"
        try:
            grasa = float(v)
        except ValueError:
            return False, "Debe ser un número"
        if grasa < RANGO_GRASA[0]:
            return False, f"Mínimo {RANGO_GRASA[0]}%"
        if grasa > RANGO_GRASA[1]:
            return False, f"Máximo {RANGO_GRASA[1]}%"
        return True, ""
