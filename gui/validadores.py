"""Reglas de validación de campos del formulario — sin dependencias de Tkinter."""


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
        if edad < 10 or edad > 100:
            return False, "Edad fuera de rango (10–100)"
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
        if peso < 20:
            return False, "Mínimo 20 kg"
        if peso > 155:
            return False, "Máximo 155 kg"
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
        if est < 100 or est > 230:
            return False, "Rango válido: 100–230 cm"
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
        if grasa < 5:
            return False, "Mínimo 5%"
        if grasa > 60:
            return False, "Máximo 60%"
        return True, ""
