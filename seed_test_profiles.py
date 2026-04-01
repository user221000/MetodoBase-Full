#!/usr/bin/env python3
"""
seed_test_profiles.py — Crea perfiles funcionales de prueba para dashboards.

Genera:
- 12 clientes con variedad de objetivos, actividad, sexo y corporales
- Historial de planes generados (2-8 por cliente) distribuidos en 60 días
- Datos de progreso (peso/grasa cambiando realísticamente)
- Estadísticas listas para KPIs del dashboard

Uso:
    python seed_test_profiles.py          # Crea perfiles de prueba
    python seed_test_profiles.py --clean  # Borra y recrea desde cero
"""
import sqlite3
import sys
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

# Agregar root al path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from config.constantes import CARPETA_REGISTROS

DB_PATH = Path(CARPETA_REGISTROS) / "clientes.db"

# ──────────────────────────────────────────────────────────────────────
# PERFILES DE PRUEBA — diseñados para cubrir todos los ejes del dashboard
# ──────────────────────────────────────────────────────────────────────

CLIENTES_SEED = [
    # ── DÉFICIT (4 clientes) ──
    {
        "id_cliente": "TEST0001",
        "nombre": "María García López",
        "telefono": "5512345001",
        "email": "maria.garcia@test.com",
        "edad": 28,
        "sexo": "F",
        "peso_kg": 72.0,
        "estatura_cm": 165.0,
        "grasa_corporal_pct": 28.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
        "plantilla_tipo": "general",
        "notas": "Quiere bajar 5 kg antes de verano",
    },
    {
        "id_cliente": "TEST0002",
        "nombre": "Carlos Hernández Ruiz",
        "telefono": "5512345002",
        "email": "carlos.hdz@test.com",
        "edad": 35,
        "sexo": "M",
        "peso_kg": 95.0,
        "estatura_cm": 178.0,
        "grasa_corporal_pct": 25.0,
        "nivel_actividad": "leve",
        "objetivo": "deficit",
        "plantilla_tipo": "general",
        "notas": "Sedentario, empezando gimnasio",
    },
    {
        "id_cliente": "TEST0003",
        "nombre": "Ana Martínez Flores",
        "telefono": "5512345003",
        "email": "ana.mtz@test.com",
        "edad": 42,
        "sexo": "F",
        "peso_kg": 68.0,
        "estatura_cm": 160.0,
        "grasa_corporal_pct": 32.0,
        "nivel_actividad": "nula",
        "objetivo": "deficit",
        "plantilla_tipo": "general",
        "notas": None,
    },
    {
        "id_cliente": "TEST0004",
        "nombre": "Roberto Díaz Sánchez",
        "telefono": "5512345004",
        "email": "roberto.diaz@test.com",
        "edad": 50,
        "sexo": "M",
        "peso_kg": 88.0,
        "estatura_cm": 175.0,
        "grasa_corporal_pct": 22.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
        "plantilla_tipo": "general",
        "notas": "Doctor le recomendó bajar de peso",
    },
    # ── MANTENIMIENTO (4 clientes) ──
    {
        "id_cliente": "TEST0005",
        "nombre": "Laura Vega Torres",
        "telefono": "5512345005",
        "email": "laura.vega@test.com",
        "edad": 25,
        "sexo": "F",
        "peso_kg": 58.0,
        "estatura_cm": 163.0,
        "grasa_corporal_pct": 22.0,
        "nivel_actividad": "intensa",
        "objetivo": "mantenimiento",
        "plantilla_tipo": "general",
        "notas": "Crossfit 5 veces/semana",
    },
    {
        "id_cliente": "TEST0006",
        "nombre": "Fernando Morales Castro",
        "telefono": "5512345006",
        "email": "fer.morales@test.com",
        "edad": 30,
        "sexo": "M",
        "peso_kg": 78.0,
        "estatura_cm": 180.0,
        "grasa_corporal_pct": 15.0,
        "nivel_actividad": "moderada",
        "objetivo": "mantenimiento",
        "plantilla_tipo": "general",
        "notas": None,
    },
    {
        "id_cliente": "TEST0007",
        "nombre": "Sofía Ramírez Ortega",
        "telefono": "5512345007",
        "email": "sofia.rami@test.com",
        "edad": 33,
        "sexo": "F",
        "peso_kg": 62.0,
        "estatura_cm": 168.0,
        "grasa_corporal_pct": 20.0,
        "nivel_actividad": "leve",
        "objetivo": "mantenimiento",
        "plantilla_tipo": "general",
        "notas": "Yoga y caminata",
    },
    {
        "id_cliente": "TEST0008",
        "nombre": "Diego Navarro Peña",
        "telefono": "5512345008",
        "email": "diego.nav@test.com",
        "edad": 22,
        "sexo": "M",
        "peso_kg": 70.0,
        "estatura_cm": 172.0,
        "grasa_corporal_pct": 14.0,
        "nivel_actividad": "intensa",
        "objetivo": "mantenimiento",
        "plantilla_tipo": "general",
        "notas": "Futbol amateur",
    },
    # ── SUPERÁVIT (4 clientes) ──
    {
        "id_cliente": "TEST0009",
        "nombre": "Alejandro Reyes Luna",
        "telefono": "5512345009",
        "email": "alex.reyes@test.com",
        "edad": 20,
        "sexo": "M",
        "peso_kg": 65.0,
        "estatura_cm": 182.0,
        "grasa_corporal_pct": 12.0,
        "nivel_actividad": "intensa",
        "objetivo": "superavit",
        "plantilla_tipo": "general",
        "notas": "Quiere ganar masa muscular, muy delgado",
    },
    {
        "id_cliente": "TEST0010",
        "nombre": "Valentina Cruz Ibarra",
        "telefono": "5512345010",
        "email": "vale.cruz@test.com",
        "edad": 27,
        "sexo": "F",
        "peso_kg": 52.0,
        "estatura_cm": 158.0,
        "grasa_corporal_pct": 18.0,
        "nivel_actividad": "moderada",
        "objetivo": "superavit",
        "plantilla_tipo": "general",
        "notas": "Busca ganar fuerza para competencia",
    },
    {
        "id_cliente": "TEST0011",
        "nombre": "Javier Méndez Ríos",
        "telefono": "5512345011",
        "email": "javi.mendez@test.com",
        "edad": 19,
        "sexo": "M",
        "peso_kg": 60.0,
        "estatura_cm": 176.0,
        "grasa_corporal_pct": 10.0,
        "nivel_actividad": "intensa",
        "objetivo": "superavit",
        "plantilla_tipo": "general",
        "notas": "Ectomorfo, necesita muchas calorías",
    },
    {
        "id_cliente": "TEST0012",
        "nombre": "Camila Rojas Vargas",
        "telefono": "5512345012",
        "email": "cami.rojas@test.com",
        "edad": 24,
        "sexo": "F",
        "peso_kg": 55.0,
        "estatura_cm": 162.0,
        "grasa_corporal_pct": 19.0,
        "nivel_actividad": "moderada",
        "objetivo": "superavit",
        "plantilla_tipo": "general",
        "notas": None,
    },
]

# Factores de actividad para cálculos Katch-McArdle
FACTORES = {"nula": 1.2, "leve": 1.375, "moderada": 1.55, "intensa": 1.725}

# Multiplicador kcal según objetivo
MULT_OBJETIVO = {"deficit": 0.80, "mantenimiento": 1.0, "superavit": 1.15}


def _calcular_macros(c: dict) -> dict:
    """Calcula TMB (Katch-McArdle), GET y macros para un perfil."""
    masa_magra = c["peso_kg"] * (1 - c["grasa_corporal_pct"] / 100)
    tmb = 370 + (21.6 * masa_magra)
    factor = FACTORES.get(c["nivel_actividad"], 1.2)
    get_total = tmb * factor
    mult = MULT_OBJETIVO.get(c["objetivo"], 1.0)
    kcal_objetivo = get_total * mult

    proteina_g = c["peso_kg"] * 2.0
    grasa_g = c["peso_kg"] * 0.8
    kcal_prot = proteina_g * 4
    kcal_grasa = grasa_g * 9
    carbs_g = max(0, (kcal_objetivo - kcal_prot - kcal_grasa) / 4)

    return {
        "tmb": round(tmb, 1),
        "get_total": round(get_total, 1),
        "kcal_objetivo": round(kcal_objetivo, 0),
        "proteina_g": round(proteina_g, 1),
        "carbs_g": round(carbs_g, 1),
        "grasa_g": round(grasa_g, 1),
    }


def _peso_progreso(peso_base: float, objetivo: str, plan_idx: int) -> float:
    """Simula cambio de peso realista según objetivo."""
    if objetivo == "deficit":
        delta = -0.3 * plan_idx + random.uniform(-0.2, 0.1)
    elif objetivo == "superavit":
        delta = 0.25 * plan_idx + random.uniform(-0.1, 0.2)
    else:
        delta = random.uniform(-0.3, 0.3)
    return round(peso_base + delta, 1)


def _grasa_progreso(grasa_base: float, objetivo: str, plan_idx: int) -> float:
    """Simula cambio de grasa realista según objetivo."""
    if objetivo == "deficit":
        delta = -0.4 * plan_idx + random.uniform(-0.2, 0.1)
    elif objetivo == "superavit":
        delta = 0.15 * plan_idx + random.uniform(-0.1, 0.15)
    else:
        delta = random.uniform(-0.2, 0.2)
    return round(max(5.0, grasa_base + delta), 1)


def seed(clean: bool = False) -> None:
    """Inserta los perfiles de prueba y su historial de planes."""
    Path(CARPETA_REGISTROS).mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    # Asegurar que tablas existen (al importar GestorBDClientes ya se crea)
    from src.gestor_bd import GestorBDClientes
    _gestor = GestorBDClientes(db_path=str(DB_PATH))
    conn.close()

    # Reabrir para insertar datos de prueba
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    if clean:
        # Eliminar solo datos de prueba (IDs que empiezan con TEST)
        cursor.execute("DELETE FROM planes_generados WHERE id_cliente LIKE 'TEST%'")
        cursor.execute("DELETE FROM clientes WHERE id_cliente LIKE 'TEST%'")
        conn.commit()
        print("[SEED] Datos de prueba anteriores eliminados")

    ahora = datetime.now()
    insertados = 0
    planes_total = 0

    for cliente in CLIENTES_SEED:
        # Verificar si ya existe
        cursor.execute(
            "SELECT 1 FROM clientes WHERE id_cliente = ?",
            (cliente["id_cliente"],),
        )
        if cursor.fetchone():
            print(f"  ⏭  {cliente['id_cliente']} ya existe, saltando...")
            continue

        # Fecha de registro: entre 60 y 5 días atrás
        dias_atras = random.randint(5, 60)
        fecha_registro = ahora - timedelta(days=dias_atras)

        macros = _calcular_macros(cliente)
        num_planes = random.randint(2, 8)

        cursor.execute(
            """
            INSERT INTO clientes
            (id_cliente, nombre, telefono, email, edad, sexo, peso_kg, estatura_cm,
             grasa_corporal_pct, nivel_actividad, objetivo, notas, plantilla_tipo,
             fecha_registro, ultimo_plan, total_planes_generados, activo,
             datos_cifrados)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (
                cliente["id_cliente"],
                cliente["nombre"],
                cliente["telefono"],
                cliente["email"],
                cliente["edad"],
                cliente["sexo"],
                cliente["peso_kg"],
                cliente["estatura_cm"],
                cliente["grasa_corporal_pct"],
                cliente["nivel_actividad"],
                cliente["objetivo"],
                cliente["notas"],
                cliente["plantilla_tipo"],
                fecha_registro.isoformat(),
                None,  # se actualiza después
                num_planes,
            ),
        )
        insertados += 1

        # Generar historial de planes distribuidos entre registro y ahora
        intervalo_dias = max(1, dias_atras // num_planes)
        ultimo_plan_fecha = None

        for i in range(num_planes):
            fecha_plan = fecha_registro + timedelta(
                days=intervalo_dias * (i + 1),
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59),
            )
            if fecha_plan > ahora:
                fecha_plan = ahora - timedelta(hours=random.randint(1, 48))

            peso_momento = _peso_progreso(cliente["peso_kg"], cliente["objetivo"], i)
            grasa_momento = _grasa_progreso(
                cliente["grasa_corporal_pct"], cliente["objetivo"], i
            )

            # Recalcular macros con peso actual
            c_momento = {**cliente, "peso_kg": peso_momento, "grasa_corporal_pct": grasa_momento}
            macros_m = _calcular_macros(c_momento)

            # Simular kcal_real con desviación realista (±2-8%)
            desv = random.uniform(0.02, 0.08)
            kcal_real = macros_m["kcal_objetivo"] * (1 + random.choice([-1, 1]) * desv)
            desv_pct = round(abs(kcal_real - macros_m["kcal_objetivo"]) / macros_m["kcal_objetivo"] * 100, 1)

            tipo_plan = random.choice(["menu_fijo", "menu_fijo", "con_opciones"])

            cursor.execute(
                """
                INSERT INTO planes_generados
                (id_cliente, fecha_generacion, tmb, get_total,
                 kcal_objetivo, kcal_real, proteina_g, carbs_g, grasa_g,
                 objetivo, nivel_actividad, ruta_pdf,
                 peso_en_momento, grasa_en_momento, desviacion_maxima_pct,
                 plantilla_tipo, tipo_plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente["id_cliente"],
                    fecha_plan.isoformat(),
                    macros_m["tmb"],
                    macros_m["get_total"],
                    macros_m["kcal_objetivo"],
                    round(kcal_real, 0),
                    macros_m["proteina_g"],
                    macros_m["carbs_g"],
                    macros_m["grasa_g"],
                    cliente["objetivo"],
                    cliente["nivel_actividad"],
                    f"registros/planes/{cliente['id_cliente']}_plan_{i+1}.pdf",
                    peso_momento,
                    grasa_momento,
                    desv_pct,
                    cliente["plantilla_tipo"],
                    tipo_plan,
                ),
            )
            planes_total += 1
            ultimo_plan_fecha = fecha_plan

        # Actualizar ultimo_plan del cliente
        if ultimo_plan_fecha:
            cursor.execute(
                "UPDATE clientes SET ultimo_plan = ? WHERE id_cliente = ?",
                (ultimo_plan_fecha.isoformat(), cliente["id_cliente"]),
            )

        print(f"  ✓ {cliente['id_cliente']} — {cliente['nombre']} "
              f"({cliente['objetivo']}, {cliente['nivel_actividad']}) "
              f"→ {num_planes} planes")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  SEED COMPLETADO")
    print(f"  Clientes insertados: {insertados}")
    print(f"  Planes generados:    {planes_total}")
    print(f"  Base de datos:       {DB_PATH}")
    print(f"{'='*60}")

    # Verificación rápida
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE id_cliente LIKE 'TEST%'")
    total_test = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM planes_generados WHERE id_cliente LIKE 'TEST%'")
    total_planes_test = cursor.fetchone()[0]
    cursor.execute("""
        SELECT objetivo, COUNT(*) FROM clientes
        WHERE id_cliente LIKE 'TEST%' AND activo = 1
        GROUP BY objetivo
    """)
    por_objetivo = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("""
        SELECT nivel_actividad, COUNT(*) FROM clientes
        WHERE id_cliente LIKE 'TEST%' AND activo = 1
        GROUP BY nivel_actividad
    """)
    por_actividad = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    print(f"\n  Verificación:")
    print(f"    Clientes TEST activos: {total_test}")
    print(f"    Planes TEST totales:   {total_planes_test}")
    print(f"    Por objetivo:          {por_objetivo}")
    print(f"    Por actividad:         {por_actividad}")
    print()


if __name__ == "__main__":
    clean = "--clean" in sys.argv
    seed(clean=clean)
