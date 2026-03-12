"""
Base de alimentos - Versión simplificada y balanceada (PRODUCCIÓN)
Esta es la fuente única de verdad para todos los alimentos y configuración.
"""

# ============================================================================
# BASE DE ALIMENTOS (proteína/carb/grasa por 100g)
# ============================================================================

ALIMENTOS_BASE = {
    # ============================================================================
    # PROTEÍNAS (20 opciones)
    # ============================================================================
    'pechuga_de_pollo':    {'proteina': 31, 'carbs': 0,   'grasa': 3.6,  'kcal': 165, 'meal_idx': [0, 1, 2, 3]},
    'carne_magra_res':     {'proteina': 26, 'carbs': 0,   'grasa': 10,   'kcal': 217, 'meal_idx': [1, 2, 3]},
    'pescado_blanco':      {'proteina': 22, 'carbs': 0,   'grasa': 2,    'kcal': 105, 'meal_idx': [1, 2, 3]},
    'salmon':              {'proteina': 20, 'carbs': 0,   'grasa': 13,   'kcal': 208, 'meal_idx': [1, 2]},
    'huevo':               {'proteina': 13, 'carbs': 1,   'grasa': 11,   'kcal': 155, 'meal_idx': [0, 1]},
    'claras_huevo':        {'proteina': 11, 'carbs': 0.7, 'grasa': 0.2,  'kcal': 52,  'meal_idx': [0, 3]},
    'queso_panela':        {'proteina': 18, 'carbs': 2,   'grasa': 18,   'kcal': 264, 'meal_idx': [0, 1, 3]},
    'yogurt_griego_light': {'proteina': 10, 'carbs': 4,   'grasa': 0.4,  'kcal': 59,  'meal_idx': [0]},
    'proteina_suero':      {'proteina': 25, 'carbs': 8,   'grasa': 6,    'kcal': 400, 'meal_idx': [0]},
    'atun_en_agua':        {'proteina': 25, 'carbs': 0,   'grasa': 1,    'kcal': 116, 'meal_idx': [1, 2, 3]},
    'pollo_muslo':         {'proteina': 25, 'carbs': 0,   'grasa': 15,   'kcal': 250, 'meal_idx': [1, 2]},
    'carne_molida_res':    {'proteina': 24, 'carbs': 0,   'grasa': 18,   'kcal': 254, 'meal_idx': [2]},
    'pavo_pechuga':        {'proteina': 24, 'carbs': 0,   'grasa': 1,    'kcal': 104, 'meal_idx': [1, 2, 3]},
    'tofu_firme':          {'proteina': 15, 'carbs': 2,   'grasa': 9,    'kcal': 144, 'meal_idx': [2, 3]},
    'requesón':            {'proteina': 11, 'carbs': 3,   'grasa': 4,    'kcal': 98,  'meal_idx': [0, 3]},
    'jamon_pavo':          {'proteina': 13, 'carbs': 1,   'grasa': 3,    'kcal': 103, 'meal_idx': [0, 1]},
    'camarones':           {'proteina': 20, 'carbs': 1,   'grasa': 1,    'kcal': 99,  'meal_idx': [2, 3]},
    'sardinas':            {'proteina': 20, 'carbs': 0,   'grasa': 10,   'kcal': 185, 'meal_idx': [1, 2]},
    'leche_descremada':    {'proteina': 3.4, 'carbs': 5,  'grasa': 0.5,  'kcal': 42,  'meal_idx': [0]},
    'yogurt_natural':      {'proteina': 5,  'carbs': 7,   'grasa': 2,    'kcal': 61,  'meal_idx': [0, 3]},

    # ============================================================================
    # CARBOHIDRATOS (18 opciones)
    # ============================================================================
    'arroz_blanco':    {'proteina': 2.7, 'carbs': 28,   'grasa': 0.3,  'kcal': 130, 'meal_idx': [1, 2, 3]},
    'arroz_integral':  {'proteina': 2.6, 'carbs': 23,   'grasa': 1,    'kcal': 111, 'meal_idx': [1, 2, 3]},
    'papa':            {'proteina': 2,   'carbs': 17,   'grasa': 0.1,  'kcal': 77,  'meal_idx': [1, 2, 3]},
    'camote':          {'proteina': 1.6, 'carbs': 20,   'grasa': 0.1,  'kcal': 86,  'meal_idx': [1, 2, 3]},
    'avena':           {'proteina': 11,  'carbs': 66,   'grasa': 7,    'kcal': 389, 'meal_idx': [0]},  # Solo desayuno
    'pan_integral':    {'proteina': 9,   'carbs': 41,   'grasa': 3.5,  'kcal': 247, 'meal_idx': [0, 3]},
    'tortilla_maiz':   {'proteina': 5.7, 'carbs': 44,   'grasa': 2.8,  'kcal': 218, 'meal_idx': [0, 1, 3]},
    'frijoles':        {'proteina': 9,   'carbs': 24,   'grasa': 0.5,  'kcal': 127, 'meal_idx': [2]}, # Solo comida
    'lentejas':        {'proteina': 8,   'carbs': 20,   'grasa': 0.4,  'kcal': 116, 'meal_idx': [1, 2]},
    'garbanzos':       {'proteina': 8,   'carbs': 20,   'grasa': 2.6,  'kcal': 164, 'meal_idx': [1, 2]},
    'pasta_integral':  {'proteina': 5,   'carbs': 31,   'grasa': 1.1,  'kcal': 124, 'meal_idx': [2]}, # Solo comida
    'quinoa':          {'proteina': 4.4, 'carbs': 21,   'grasa': 1.9,  'kcal': 120, 'meal_idx': [2, 3]},
    'elote':           {'proteina': 3.3, 'carbs': 19,   'grasa': 1.4,  'kcal': 86,  'meal_idx': [1, 2]},
    'platano_macho':   {'proteina': 1.3, 'carbs': 32,   'grasa': 0.4,  'kcal': 122, 'meal_idx': [1, 2]},
    'tortilla_harina': {'proteina': 8,   'carbs': 49,   'grasa': 8,    'kcal': 304, 'meal_idx': [0, 1, 3]},
    'pan_blanco':      {'proteina': 8.5, 'carbs': 49,   'grasa': 3.2,  'kcal': 265, 'meal_idx': [0]},
    'cereal_integral': {'proteina': 10,  'carbs': 67,   'grasa': 3,    'kcal': 350, 'meal_idx': [0]},
    'granola':         {'proteina': 10,  'carbs': 68,   'grasa': 8,    'kcal': 471, 'meal_idx': [0]},

    # ============================================================================
    # GRASAS (9 opciones)
    # ============================================================================
    'aceite_de_oliva':   {'proteina': 0,  'carbs': 0,  'grasa': 100, 'kcal': 900, 'meal_idx': [0, 1, 2, 3]},
    'aguacate':          {'proteina': 2,  'carbs': 9,  'grasa': 15,  'kcal': 160, 'meal_idx': [0, 1, 2]},
    'nueces':            {'proteina': 15, 'carbs': 14, 'grasa': 65,  'kcal': 654, 'meal_idx': [0, 3]},
    'almendras':         {'proteina': 21, 'carbs': 22, 'grasa': 49,  'kcal': 579, 'meal_idx': [0, 3]},
    'mantequilla_mani':  {'proteina': 25, 'carbs': 20, 'grasa': 50,  'kcal': 588, 'meal_idx': [0, 2]},
    'aceite_de_aguacate': {'proteina': 0, 'carbs': 0,  'grasa': 100, 'kcal': 900, 'meal_idx': [1, 2, 3]},
    'semillas_chia':     {'proteina': 17, 'carbs': 42, 'grasa': 31,  'kcal': 486, 'meal_idx': [0]},
    'aceite_coco':       {'proteina': 0,  'carbs': 0,  'grasa': 99,  'kcal': 862, 'meal_idx': [0, 1]},
    'crema_cacahuate':   {'proteina': 22, 'carbs': 21, 'grasa': 51,  'kcal': 588, 'meal_idx': [0]},

    # ============================================================================
    # VERDURAS (20 opciones)
    # ============================================================================
    'brocoli':       {'proteina': 2.8, 'carbs': 7,   'grasa': 0.4, 'kcal': 34, 'meal_idx': [0, 1, 2, 3]},
    'espinaca':      {'proteina': 2.9, 'carbs': 3.6, 'grasa': 0.4, 'kcal': 23, 'meal_idx': [0, 1, 2, 3]},
    'calabacita':    {'proteina': 1.2, 'carbs': 3.1, 'grasa': 0.3, 'kcal': 17, 'meal_idx': [1, 2, 3]},
    'champiñones':   {'proteina': 3.1, 'carbs': 3.3, 'grasa': 0.3, 'kcal': 22, 'meal_idx': [1, 2, 3]},
    'coliflor':      {'proteina': 1.9, 'carbs': 5,   'grasa': 0.3, 'kcal': 25, 'meal_idx': [2, 3]},
    'zanahoria':     {'proteina': 0.9, 'carbs': 10,  'grasa': 0.2, 'kcal': 41, 'meal_idx': [1, 2]},
    'apio':          {'proteina': 0.7, 'carbs': 3,   'grasa': 0.2, 'kcal': 16, 'meal_idx': [1, 2, 3]},
    'pepino':        {'proteina': 0.7, 'carbs': 4,   'grasa': 0.1, 'kcal': 16, 'meal_idx': [1, 2, 3]},
    'tomate':        {'proteina': 0.9, 'carbs': 4,   'grasa': 0.2, 'kcal': 18, 'meal_idx': [1, 2, 3]},
    'lechuga':       {'proteina': 1.4, 'carbs': 3,   'grasa': 0.2, 'kcal': 15, 'meal_idx': [1, 2, 3]},
    'cebolla':       {'proteina': 1.1, 'carbs': 9,   'grasa': 0.1, 'kcal': 40, 'meal_idx': [1, 2, 3]},
    'pimiento':      {'proteina': 1,   'carbs': 6,   'grasa': 0.3, 'kcal': 27, 'meal_idx': [1, 2, 3]},
    'ejotes':        {'proteina': 1.8, 'carbs': 7,   'grasa': 0.1, 'kcal': 31, 'meal_idx': [2, 3]},
    'acelgas':       {'proteina': 1.8, 'carbs': 4,   'grasa': 0.2, 'kcal': 19, 'meal_idx': [2, 3]},
    'berza':         {'proteina': 3.3, 'carbs': 6,   'grasa': 0.7, 'kcal': 35, 'meal_idx': [2, 3]},
    'nopales':       {'proteina': 1.3, 'carbs': 4,   'grasa': 0.3, 'kcal': 23, 'meal_idx': [1, 2]},
    'chile_poblano': {'proteina': 1.5, 'carbs': 7,   'grasa': 0.6, 'kcal': 30, 'meal_idx': [2]},
    'col_morada':    {'proteina': 1.4, 'carbs': 7,   'grasa': 0.2, 'kcal': 31, 'meal_idx': [2, 3]},
    'rabano':        {'proteina': 0.7, 'carbs': 2,   'grasa': 0.1, 'kcal': 16, 'meal_idx': [1, 2, 3]},
    'chayote':       {'proteina': 0.8, 'carbs': 5,   'grasa': 0.3, 'kcal': 25, 'meal_idx': [2, 3]},

    # ============================================================================
    # FRUTAS (18 opciones - solo desayuno y cena)
    # ============================================================================
    'manzana':       {'proteina': 0.3, 'carbs': 14,  'grasa': 0.2, 'kcal': 52, 'meal_idx': [0, 3]},
    'platano':       {'proteina': 1.1, 'carbs': 27,  'grasa': 0.3, 'kcal': 89, 'meal_idx': [0, 3]},
    'papaya':        {'proteina': 0.6, 'carbs': 12,  'grasa': 0.1, 'kcal': 43, 'meal_idx': [0, 3]},
    'naranja':       {'proteina': 0.7, 'carbs': 12,  'grasa': 0.1, 'kcal': 47, 'meal_idx': [0, 3]},
    'mango':         {'proteina': 0.7, 'carbs': 15,  'grasa': 0.3, 'kcal': 60, 'meal_idx': [0, 3]},
    'melon':         {'proteina': 0.9, 'carbs': 8,   'grasa': 0.2, 'kcal': 34, 'meal_idx': [0, 3]},
    'piña':          {'proteina': 0.5, 'carbs': 13,  'grasa': 0.1, 'kcal': 50, 'meal_idx': [0, 3]},
    'pera':          {'proteina': 0.4, 'carbs': 15,  'grasa': 0.1, 'kcal': 57, 'meal_idx': [0, 3]},
    'fresas':        {'proteina': 0.7, 'carbs': 8,   'grasa': 0.3, 'kcal': 32, 'meal_idx': [0, 3]},
    'kiwi':          {'proteina': 1.1, 'carbs': 15,  'grasa': 0.5, 'kcal': 61, 'meal_idx': [0, 3]},
    'sandia':        {'proteina': 0.6, 'carbs': 8,   'grasa': 0.2, 'kcal': 30, 'meal_idx': [0, 3]},
    'uvas':          {'proteina': 0.6, 'carbs': 17,  'grasa': 0.2, 'kcal': 67, 'meal_idx': [0, 3]},
    'mandarina':     {'proteina': 0.8, 'carbs': 13,  'grasa': 0.3, 'kcal': 53, 'meal_idx': [0, 3]},
    'durazno':       {'proteina': 0.9, 'carbs': 10,  'grasa': 0.3, 'kcal': 39, 'meal_idx': [0, 3]},
    'ciruelas':      {'proteina': 0.7, 'carbs': 11,  'grasa': 0.3, 'kcal': 46, 'meal_idx': [0, 3]},
    'guayaba':       {'proteina': 2.6, 'carbs': 14,  'grasa': 1,   'kcal': 68, 'meal_idx': [0, 3]},
    'tuna':          {'proteina': 0.7, 'carbs': 10,  'grasa': 0.5, 'kcal': 41, 'meal_idx': [0, 3]},
    'granada':       {'proteina': 1.7, 'carbs': 19,  'grasa': 1.2, 'kcal': 83, 'meal_idx': [0, 3]},
}


# ============================================================================
# LÍMITES POR COMIDA (gramos) - SIMPLIFICADOS Y REALISTAS
# ============================================================================

LIMITES_ALIMENTOS = {
    # Proteínas magras - máximo 250g
    'pechuga_de_pollo':    250,
    'carne_magra_res':     250,
    'pescado_blanco':      200,    # Máximo 200g
    'salmon':              150,    # Máximo 150g (mínimo 100g manejado en validación)
    'huevo':               170,    # Control especial: máx 2-4 huevos
    'claras_huevo':        250,    # Para cuando se sobrepasa huevo
    'queso_panela':        150,    # Lácteo: menos volumen
    'yogurt_griego_light': 200,    # Lácteo: menos volumen
    'proteina_suero':      40,     # Polvo: porciones pequeñas
    
    # Carbohidratos densos - máximo 250g (casi medio plato)
    'arroz_blanco':        250,
    'arroz_integral':      250,
    'papa':                250,
    'camote':              250,
    'avena':               150,    # Menos (muy denso)
    'pan_integral':        100,    # Menos (muy denso)
    'tortilla_maiz':       150,    # Porción realista: ~6-8 tortillas
    
    # Grasas - muy concentradas, poco volumen
    'aceite_de_oliva':     20,     # ~1 cucharada sopera
    'aguacate':            150,    # ~1 aguacate
    'nueces':              50,     # ~10-12 nueces
    'almendras':           50,     # ~15-20 almendras
    'mantequilla_mani':    40,     # ~2 cucharadas
    
    # Verduras - casi ilimitadas (< 100 kcal por 200g)
    'brocoli':            150,     # Limitado a 150g
    'espinaca':           120,     # Limitado a 120g
    'calabacita':         200,     # Limitado a 200g
    'champiñones':        150,     # Limitado a 150g
    'coliflor':           120,     # Limitado a 120g
    
    # Frutas - solo desayuno y cena, máximo 100g
    'manzana':            100,     # ≈ 1-2 manzanas medianas
    'platano':            100,     # ≈ 1-2 plátanos medianos
    'banana':             100,     # ≈ 1-2 bananas medianas (alias de platano)
    'papaya':             100,     # ≈ 1 taza
    'naranja':            100,     # ≈ 1-2 naranjas
    'mango':              150,     # ≈ 1 mango mediano
    'melon':              100,     # ≈ 1 taza
    'piña':               100,     # ≈ 1 taza
}

# ============================================================================
# EQUIVALENCIAS PRÁCTICAS (para que el usuario entienda las porciones)
# ============================================================================

EQUIVALENCIAS_PRACTICAS = {
    # Proteínas
    'pechuga_de_pollo':    '≈ 1 pechuga mediana',
    'carne_magra_res':     '≈ 1 bistec mediano',
    'pescado_blanco':      '≈ 1 fillete mediano',
    'salmon':              '≈ 1 fillete de salmón',
    'huevo':               '≈ 2-4 huevos',
    'claras_huevo':        '≈ 8-9 claras',
    'queso_panela':        '≈ 1 porción mediana',
    'yogurt_griego_light': '≈ 1 taza (200ml)',
    'proteina_suero':      '≈ 1 scoop (cucharada)',
    
    # Carbohidratos
    'arroz_blanco':        '≈ 0.5 taza cocida',
    'arroz_integral':      '≈ 0.5 taza cocida',
    'papa':                '≈ 1-2 papas medianas',
    'camote':              '≈ 1 camote mediano',
    'avena':               '≈ 0.3 taza cruda (puñado)',
    'pan_integral':        '≈ 2 rebanadas',
    'tortilla_maiz':       '≈ 6-8 tortillas',
    'banana':              '≈ 1 banana mediana',
    'frijoles':            '≈ 0.5 taza cocida',
    
    # Grasas
    'aceite_de_oliva':     '≈ 1 cucharada',
    'aguacate':            '≈ 0.5 aguacate',
    'nueces':              '≈ 15-20 nueces',
    'almendras':           '≈ 25-30 almendras',
    'mantequilla_mani':    '≈ 2 cucharadas',
    
    # Verduras
    'brocoli':             '≈ 2-3 puños cerrados',
    'espinaca':            '≈ 1-2 platos',
    'calabacita':          '≈ 1 calabacita pequeña',
    'champiñones':         '≈ 1 puñado grande',
    'coliflor':            '≈ 1 taza',
    
    # Frutas
    'manzana':             '≈ 1-2 manzanas medianas',
    'platano':             '≈ 1 plátano mediano',
    'papaya':              '≈ 1 taza',
    'naranja':             '≈ 1-2 naranjas',
    'mango':               '≈ 1 mango mediano',
    'melon':               '≈ 1 taza',
    'piña':                '≈ 1 taza',
}

# ============================================================================
# CATEGORÍAS DE ALIMENTOS (para rotación y selección)
# ============================================================================

CATEGORIAS = {
    'proteina': [
        'pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon', 'huevo',
        'claras_huevo', 'queso_panela', 'yogurt_griego_light', 'proteina_suero',
        'atun_en_agua', 'pollo_muslo', 'carne_molida_res', 'pavo_pechuga',
        'tofu_firme', 'requesón', 'jamon_pavo', 'camarones', 'sardinas',
        'leche_descremada', 'yogurt_natural',
    ],
    'carbs': [
        'arroz_blanco', 'arroz_integral', 'papa', 'camote', 'avena',
        'pan_integral', 'tortilla_maiz', 'frijoles', 'lentejas', 'garbanzos',
        'pasta_integral', 'quinoa', 'elote', 'platano_macho', 'tortilla_harina',
        'pan_blanco', 'cereal_integral', 'granola',
    ],
    'grasa': [
        'aceite_de_oliva', 'aguacate', 'nueces', 'almendras', 'mantequilla_mani',
        'aceite_de_aguacate', 'semillas_chia', 'aceite_coco', 'crema_cacahuate',
    ],
    'verdura': [
        'brocoli', 'espinaca', 'calabacita', 'champiñones', 'coliflor',
        'zanahoria', 'apio', 'pepino', 'tomate', 'lechuga', 'cebolla',
        'pimiento', 'ejotes', 'acelgas', 'berza', 'nopales', 'chile_poblano',
        'col_morada', 'rabano', 'chayote',
    ],
    'fruta': [
        'manzana', 'platano', 'papaya', 'naranja', 'mango', 'melon', 'piña',
        'pera', 'fresas', 'kiwi', 'sandia', 'uvas', 'mandarina', 'durazno',
        'ciruelas', 'guayaba', 'tuna', 'granada',
    ],
}

# ============================================================================
# REGLAS DE PENALIZACIÓN (Qué NO se puede repetir en el mismo día)
# ============================================================================

REGLAS_PENALIZACION = {
    'huevo': 1,                    # Max 1x día (huevo + claras = grupo)
    'claras_huevo': 1,             # Max 1x día
    'salmon': 1,                   # Max 1x día (muy graso)
    'carne_magra_res': 1,          # Max 1x día (rojo)
    'pechuga_de_pollo': 2,         # Max 2x día (pollo es versátil)
    'pescado_blanco': 1,           # Max 1x día
    'aceite_de_oliva': 1,          # Max 1x día (grasa concentrada)
}

# ============================================================================
# ROTACIONES POR COMIDA (Orden de preferencia)
# ============================================================================

ROTACIONES = {
    'desayuno': {
        'proteina': ['proteina_suero', 'yogurt_griego_light', 'huevo', 'claras_huevo', 'queso_panela'],
        'carbs': ['avena', 'pan_integral', 'tortilla_maiz'],
        'grasa': ['aceite_de_oliva', 'nueces', 'almendras'],
        'verdura': ['brocoli', 'espinaca'],
        'fruta': ['platano', 'manzana', 'papaya', 'naranja', 'mango', 'melon', 'piña'],
    },
    'comida': {
        'proteina': ['pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon'],
        'carbs': ['arroz_blanco', 'arroz_integral', 'papa', 'camote', 'tortilla_maiz'],
        'grasa': ['aguacate', 'nueces', 'mantequilla_mani'],
        'verdura': ['espinaca', 'calabacita', 'champiñones'],
    },
    'cena': {
        'proteina': ['pechuga_de_pollo', 'pescado_blanco', 'claras_huevo', 'queso_panela'],
        'carbs': ['papa', 'camote', 'pan_integral'],
        'grasa': ['nueces', 'almendras'],
        'verdura': ['calabacita', 'coliflor', 'brocoli'],
        'fruta': ['manzana', 'papaya', 'naranja', 'melon', 'piña', 'platano', 'mango'],
    },
}
