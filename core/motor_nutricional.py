"""
CAPA 1: Motor Nutricional (Katch-McArdle, GET, Macros)
CAPA 2: Ajuste Calórico Mensual
"""
from dataclasses import dataclass
from utils.helpers import cargar_plan_anterior_cliente


# ============================================================================
# ALERTAS DE SALUD
# ============================================================================

@dataclass
class AlertaSalud:
    """Representa una alerta de salud que la GUI puede mostrar al usuario."""
    nivel: str          # 'warning' | 'error'
    codigo: str         # identificador único de la alerta
    mensaje: str        # texto legible para el usuario
    detalle: str = ''   # información adicional técnica


class MotorNutricional:
    """Calcula masa magra, TMB, GET, objetivo de calorías y macronutrientes."""
    
    @staticmethod
    def calcular_masa_magra(peso_kg: float, grasa_pct: float) -> float:
        """Fórmula #5: masa_magra = peso * (1 - %grasa / 100)"""
        return peso_kg * (1 - grasa_pct / 100)
    
    @staticmethod
    def calcular_tmb(masa_magra: float) -> float:
        """Fórmula #6 (Katch-McArdle): TMB = 370 + (21.6 * masa_magra)"""
        return 370 + (21.6 * masa_magra)
    
    @staticmethod
    def calcular_get(tmb: float, factor_actividad: float) -> float:
        """Fórmula #7: GET = TMB * factor_actividad"""
        return tmb * factor_actividad
    
    @staticmethod
    def calcular_kcal_objetivo(get_total: float, objetivo: str) -> float:
        """
        Fórmula #8: Ajusta GET según objetivo.
        déficit: GET * 0.85 | mantenimiento: GET | superávit: GET * 1.10
        """
        objetivo = objetivo.lower().strip()
        if objetivo == 'deficit':
            return get_total * 0.85
        elif objetivo == 'superavit':
            return get_total * 1.10
        else:
            return get_total
    
    @staticmethod
    def calcular_macros(peso_kg: float, kcal_objetivo: float) -> dict:
        """
        Fórmula #9: Proteína = 1.8g * peso => kcal = proteína * 4
        Fórmula #10: Grasas = 0.8g * peso => kcal = grasas * 9
        Fórmula #11: Carbohidratos = kcal_restantes / 4

        Incluye detección de alertas de salud:
        - Déficit > 25 %
        - Carbohidratos < 0.5 g/kg tras ajuste de grasa
        """
        alertas: list[AlertaSalud] = []

        proteina_g = 1.8 * peso_kg
        kcal_proteína = proteina_g * 4
        
        grasa_g = 0.8 * peso_kg
        kcal_grasa = grasa_g * 9
        
        kcal_restantes = kcal_objetivo - (kcal_proteína + kcal_grasa)
        carbs_g = kcal_restantes / 4
        kcal_carbs = carbs_g * 4
        
        # Ajuste si carbs < 0: reducir grasa a 0.6 g/kg
        if carbs_g < 0:
            grasa_g = 0.6 * peso_kg
            kcal_grasa = grasa_g * 9
            kcal_restantes = kcal_objetivo - (kcal_proteína + kcal_grasa)
            carbs_g = kcal_restantes / 4
            kcal_carbs = carbs_g * 4

        # --- Alertas de salud ---
        # 1) Carbohidratos < 0.5 g/kg tras ajuste
        if carbs_g < (0.5 * peso_kg):
            alertas.append(AlertaSalud(
                nivel='warning',
                codigo='CARBS_MUY_BAJOS',
                mensaje=(
                    f'Carbohidratos muy bajos: {carbs_g:.1f}g '
                    f'(mínimo recomendado: {0.5 * peso_kg:.1f}g para {peso_kg:.0f}kg)'
                ),
                detalle=(
                    'Los carbohidratos cayeron por debajo de 0.5 g/kg tras el '
                    'ajuste de grasa. Considera aumentar las calorías objetivo o '
                    'reducir el déficit.'
                ),
            ))

        return {
            'proteina_g': proteina_g,
            'grasa_g': grasa_g,
            'carbs_g': carbs_g,
            'kcal_proteína': kcal_proteína,
            'kcal_grasa': kcal_grasa,
            'kcal_carbs': kcal_carbs,
            'alertas': alertas,
        }
    
    @classmethod
    def calcular_motor(cls, cliente) -> object:
        """Ejecuta todo el flujo: masa magra => TMB => GET => kcal_objetivo => macros.

        Además genera alertas de salud:
        - Déficit > 25 % respecto al GET
        - Carbohidratos < 0.5 g/kg
        Las alertas se almacenan en ``cliente.alertas_salud``.
        """
        cliente.masa_magra = cls.calcular_masa_magra(cliente.peso_kg, cliente.grasa_corporal_pct)
        cliente.tmb = cls.calcular_tmb(cliente.masa_magra)
        cliente.get_total = cls.calcular_get(cliente.tmb, cliente.factor_actividad)
        cliente.kcal_objetivo = cls.calcular_kcal_objetivo(cliente.get_total, cliente.objetivo)
        
        macros = cls.calcular_macros(cliente.peso_kg, cliente.kcal_objetivo)
        cliente.proteina_g = macros['proteina_g']
        cliente.grasa_g = macros['grasa_g']
        cliente.carbs_g = macros['carbs_g']
        cliente.kcal_proteína = macros['kcal_proteína']
        cliente.kcal_grasa = macros['kcal_grasa']
        cliente.kcal_carbs = macros['kcal_carbs']

        # --- Alertas de salud ---
        alertas: list[AlertaSalud] = list(macros.get('alertas', []))

        # Déficit > 25 %
        if cliente.get_total > 0:
            deficit_pct = (1 - cliente.kcal_objetivo / cliente.get_total) * 100
            if deficit_pct > 25:
                alertas.append(AlertaSalud(
                    nivel='error',
                    codigo='DEFICIT_EXCESIVO',
                    mensaje=(
                        f'Déficit calórico excesivo: {deficit_pct:.1f}% '
                        f'(máximo recomendado: 25%)'
                    ),
                    detalle=(
                        f'GET={cliente.get_total:.0f} kcal, '
                        f'Objetivo={cliente.kcal_objetivo:.0f} kcal. '
                        'Un déficit superior al 25% puede provocar pérdida '
                        'de masa muscular y efectos metabólicos negativos.'
                    ),
                ))

        cliente.alertas_salud = alertas
        return cliente


class AjusteCaloricoMensual:
    """
    CAPA 2: Ajuste calórico mensual basado en progreso del cliente.
    
    RESPONSABILIDAD ÚNICA: Aplicar lógica de ajuste 5% una sola vez hasta cambio de peso.
    """
    
    MARGEN_TOLERANCIA_PESO = 0.3
    FACTOR_AJUSTE_DEFICIT = 0.95
    FACTOR_AJUSTE_SUPERAVIT = 1.05
    
    @staticmethod
    def aplicar_ajuste(
        cliente_id: str,
        peso_actual: float,
        objetivo: str,
        kcal_objetivo_base: float,
        plan_anterior: dict | None = None,
        directorio_planes: str = "."
    ) -> tuple[float, bool]:
        """
        Calcula ajuste calórico mensual basado en progreso del cliente.
        
        REGLAS:
        - Peso NO cambió (<0.3kg) + déficit → reduce 5%
        - Peso NO cambió (<0.3kg) + superávit → aumenta 5%
        - Peso NO cambió (<0.3kg) + mantenimiento → mantiene
        - Peso cambió (≥0.3kg) → recalcula normal, resetea ajuste
        """
        if plan_anterior is None:
            plan_anterior = cargar_plan_anterior_cliente(cliente_id, directorio_planes)
        
        if plan_anterior is None:
            return kcal_objetivo_base, False
        
        meta_anterior = plan_anterior.get('metadata_mes_anterior', {})
        peso_base_mes_anterior = meta_anterior.get('peso_base_mes')
        ajuste_aplicado_anterior = meta_anterior.get('ajuste_aplicado', False)
        
        if peso_base_mes_anterior is None:
            return kcal_objetivo_base, False
        
        diferencia_peso = abs(peso_actual - peso_base_mes_anterior)
        peso_sin_cambio = diferencia_peso < AjusteCaloricoMensual.MARGEN_TOLERANCIA_PESO
        
        if peso_sin_cambio:
            if ajuste_aplicado_anterior:
                return kcal_objetivo_base, False
            else:
                if objetivo == "deficit":
                    return kcal_objetivo_base * AjusteCaloricoMensual.FACTOR_AJUSTE_DEFICIT, True
                elif objetivo == "superavit":
                    return kcal_objetivo_base * AjusteCaloricoMensual.FACTOR_AJUSTE_SUPERAVIT, True
                elif objetivo == "mantenimiento":
                    return kcal_objetivo_base, False
        
        return kcal_objetivo_base, False
