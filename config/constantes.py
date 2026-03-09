"""Constantes y configuración global del sistema Método Base."""
import os
from pathlib import Path

from utils.helpers import resource_path


# ============================================================================
# CLASIFICACIÓN DE PROTEÍNAS Y GRASAS PARA COMPOSICIÓN DE COMIDAS
# ============================================================================

LEAN_PROTEINS = {
    "pechuga_de_pollo",
    "pescado_blanco",
    "atun",
    "claras_huevo"
}

FATTY_PROTEINS = {
    "salmon",
    "huevo",
    "carne_molida",
    "carne_magra_res"
}

LIGHT_FATS = {
    "aceite_de_oliva",
    "aceite_de_aguacate"
}

HEAVY_FATS = {
    "mantequilla_mani",
    "almendras",
    "nueces",
    "aguacate"
}

PROTEIN_FOODS = LEAN_PROTEINS | FATTY_PROTEINS | {
    "queso_panela", "proteina_suero", "yogurt_griego_light", "pescado_blanco", "carne_magra_res"
}


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

FACTORES_ACTIVIDAD = {
    'nula': 1.2,
    'leve': 1.375,
    'moderada': 1.55,
    'intensa': 1.725,
}

OBJETIVOS_VALIDOS = {'deficit', 'mantenimiento', 'superavit'}

NIVELES_ACTIVIDAD = {'nula', 'leve', 'moderada', 'intensa'}

# Modo estricto: Si True, desviación > 5% invalida el plan; si False, solo warning
MODO_ESTRICTO = True


# ============================================================================
# HORARIOS DE COMIDAS RECOMENDADOS
# ============================================================================

HORARIOS_COMIDAS = {
    'desayuno': {
        'hora_ideal': '07:00',
        'rango': '07:00 - 08:30',
        'contexto': 'primera cosa en la mañana',
        'flexibilidad': '±1-2 horas'
    },
    'almuerzo': {
        'hora_ideal': '12:30',
        'rango': '12:30 - 13:30',
        'contexto': 'media mañana/mediodía',
        'flexibilidad': '±30-60 min'
    },
    'comida': {
        'hora_ideal': '15:00',
        'rango': '15:00 - 16:00',
        'contexto': 'post-entreno (si aplica)',
        'flexibilidad': '±30-60 min'
    },
    'cena': {
        'hora_ideal': '19:30',
        'rango': '19:30 - 20:30',
        'contexto': 'última comida del día (2-3h antes de dormir)',
        'flexibilidad': '±30-60 min'
    }
}


# ============================================================================
# EXPLICACIÓN DE OBJETIVOS
# ============================================================================

EXPLICACION_OBJETIVOS = {
    'deficit': {
        'descripcion': 'DÉFICIT CALÓRICO (PERDER GRASA)',
        'calculo': 'Calorías: -15% vs mantenimiento',
        'proteina_razon': 'Proteína alta (1.8g/kg) preserva músculo durante pérdida de peso',
        'resultado_esperado': '-0.5kg/semana (grasa)',
        'duracion': '8-12 semanas máximo, luego descanso de 4-8 semanas',
        'notas': [
            'Come en déficit para reducir grasa corporal',
            'Mantén proteína alta para no perder músculo',
            'El cardio está OK, no es obligatorio',
            'Duerme bien (7-9 horas) para recuperación'
        ]
    },
    'mantenimiento': {
        'descripcion': 'MANTENIMIENTO (PRESERVAR PESO)',
        'calculo': 'Calorías: ~GET (ajustadas a tu actividad)',
        'proteina_razon': 'Proteína moderada-alta (1.8g/kg) para mantener masa muscular',
        'resultado_esperado': '±0kg/mes (peso estable)',
        'duracion': 'Indefinido, es tu baseline',
        'notas': [
            'Come matching your activity level',
            'Proteína suficiente para mantener músculos',
            'Ideal para "recomp" si es nuevo en gym'
        ]
    },
    'superavit': {
        'descripcion': 'SUPERÁVIT CALÓRICO (GANAR MASA)',
        'calculo': 'Calorías: +10% vs mantenimiento',
        'proteina_razon': 'Proteína alta (1.8g/kg) construcción de nuevo tejido muscular',
        'resultado_esperado': '+0.5kg/semana (incluye %agua y grasa)',
        'duracion': '8-12 semanas, luego déficit para "definir"',
        'notas': [
            'Come en superávit para ganar masa muscular',
            'Proteína es CRÍTICA para crecimiento',
            'Entreno de fuerza es OBLIGATORIO (pesas)',
            'Ganancia de grasa es normal (~20-30% de ganancia total)'
        ]
    }
}


# ============================================================================
# RUTAS PARA PDF
# ============================================================================

try:
    documentos_dir = str(Path.home() / "Documents")
except Exception:
    documentos_dir = os.path.expanduser("~")

CARPETA_SALIDA = os.path.join(documentos_dir, "PlanesPDF")
os.makedirs(CARPETA_SALIDA, exist_ok=True)

RUTA_LOGO = resource_path("assets/logo.png")


# ============================================================================
# MÍNIMOS REALISTAS POR ALIMENTO
# ============================================================================

MINIMOS_POR_ALIMENTO = {
    'avena': 40,
    'pan_integral': 50,
    'pan_blanco': 50,
    'tortilla_maiz': 2,
    'banana': 100,
    'arroz_blanco': 50,
    'arroz_integral': 50,
    'papa': 80,
    'camote': 80,
    'salmon': 100,
    'pescado_blanco': 80,
    'pechuga_de_pollo': 80,
    'carne_magra_res': 90,
    'almendras': 20,
    'nueces': 20,
    'aguacate': 80,
}


# ============================================================================
# ALIMENTOS CON LÍMITES ESTRICTOS (sin expansión permitida, máximo 200g)
# ============================================================================

ALIMENTOS_LIMITE_ESTRICTO = {'frijoles'}


# ============================================================================
# LÍMITES DUROS POR ALIMENTO (máx expansión 1.2x)
# ============================================================================

LIMITES_DUROS_ALIMENTOS = {
    # PROTEÍNAS (g por comida)
    'huevo':               200,   # ~4 huevos
    'pechuga_de_pollo':    200,
    'carne_magra_res':     180,
    'pescado_blanco':      200,
    'salmon':              150,   # más caro
    'claras_huevo':        300,
    'queso_panela':        100,
    'yogurt_griego_light': 200,
    'yogurt':              200,
    'proteina_suero':       40,   # ~1 scoop
    # CARBOHIDRATOS
    'arroz_blanco':        200,   # ~2 tazas cocido
    'arroz_integral':      200,
    'papa':                250,
    'camote':              250,
    'avena':               100,   # ~1 taza
    'pan_integral':        100,   # ~3 rebanadas
    'tortilla_maiz':       120,   # ~4 tortillas
    'frijoles':            250,   # muy económico y nutritivo
    'lentejas':            200,
    'banana':              200,   # ~2 bananas
    'platano':             200,
    # GRASAS
    'aguacate':            100,   # ~1 aguacate mediano
    'nueces':               40,
    'almendras':            40,
    'aceite_de_oliva':      20,   # ~2 cucharadas
    'mantequilla_mani':     30,
    # VEGETALES (fibra, sin límite estricto)
    'brocoli':             300,
    'espinaca':            300,
    'lechuga_romana':      300,
    'pepino':              300,
    'tomate':              300,
    'zanahoria':           300,
    'calabaza':            300,
    'calabacita':          300,
    'col':                 300,
}


# ============================================================================
# FRECUENCIA MÁXIMA SEMANAL POR ALIMENTO
# ============================================================================

FRECUENCIA_MAXIMA_SEMANAL: dict[str, int] = {
    # Alimentos de costo elevado o ingesta limitada
    'salmon':          2,
    'aguacate':        4,
    'proteina_suero':  5,
    'nueces':          5,
    'almendras':       5,
    # Alimentos económicos: sin restricción práctica
    'frijoles':       99,
    'lentejas':       99,
    'huevo':          99,
    'arroz_blanco':   99,
    'arroz_integral': 99,
    'papa':           99,
    'camote':         99,
    'avena':          99,
    'tortilla_maiz':  99,
}


# ============================================================================
# CLASIFICACIÓN ESTRUCTURAL DE ALIMENTOS
# ============================================================================

PROTEINAS_ESTRUCTURALES = {
    'pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon'
}

PROTEINAS_MIXTAS = {
    'huevo', 'yogurt', 'frijoles', 'lentejas', 'queso_panela'
}

CARBOS_DENSOS = {
    'arroz_blanco', 'arroz_integral', 'papa', 'camote'
}

CARBOS_SECUNDARIOS = {
    'pan_integral', 'tortilla_maiz', 'avena', 'banana'
}

LEGUMINOSAS = {
    'frijoles', 'lentejas', 'garbanzos'
}


# ============================================================================
# LÍMITES PORCENTUALES DE KCAL POR COMIDA
# ============================================================================

LIMITES_PORCENTUALES_KCAL = {
    'proteina_principal': 0.45,
    'carb_principal': 0.50,
    'grasas_puras': 0.30,
    'leguminosas': 0.35,
}
