#!/usr/bin/env python3
"""
seed_dashboard_data.py — Seed 200+ clients and 300-500 plans for realistic dashboard.

Creates diverse client profiles and plan history with realistic distributions.
Uses the SQLAlchemy ORM models and engine directly.

Usage:
    python seed_dashboard_data.py           # Add new seed data
    python seed_dashboard_data.py --clean   # Reset seed data first
"""
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from web.database.engine import init_db, get_engine
from web.database.models import Base, Cliente, PlanGenerado

import logging

logger = logging.getLogger(__name__)
from sqlalchemy.orm import sessionmaker

GYM_ID = "6e4c92f0-ac49-4a5b-93de-8d7342f39c5e"

# ── Name pools ───────────────────────────────────────────────────────────────

NOMBRES_M = [
    "Carlos", "Miguel", "José", "Luis", "Juan", "Fernando", "Ricardo", "Eduardo",
    "Andrés", "Diego", "Alejandro", "Daniel", "Pedro", "Roberto", "Sergio",
    "Pablo", "Javier", "Rafael", "Óscar", "Arturo", "Gabriel", "Iván",
    "Héctor", "Manuel", "Raúl", "Enrique", "Francisco", "Alberto", "Hugo",
    "Mario", "Gustavo", "Emilio", "Adrián", "Víctor", "Ignacio",
]

NOMBRES_F = [
    "María", "Ana", "Sofía", "Laura", "Carmen", "Valentina", "Lucía", "Paula",
    "Andrea", "Daniela", "Gabriela", "Isabella", "Mariana", "Fernanda", "Karen",
    "Diana", "Patricia", "Claudia", "Rosa", "Mónica", "Elena", "Alejandra",
    "Natalia", "Camila", "Verónica", "Paola", "Sandra", "Teresa", "Liliana",
    "Karla", "Jimena", "Regina", "Julieta", "Silvia", "Estefanía",
]

APELLIDOS = [
    "García", "Hernández", "Martínez", "López", "González", "Rodríguez",
    "Pérez", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera",
    "Gómez", "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez",
    "Ortiz", "Ramos", "Vargas", "Castillo", "Jiménez", "Mendoza",
    "Ruiz", "Aguilar", "Herrera", "Medina", "Castro", "Romero",
    "Vega", "Delgado", "Ávila", "Guerrero", "Contreras", "Figueroa",
    "Salazar", "Mejía", "Cortés", "Fuentes", "Navarro", "Acosta",
]

OBJETIVOS = ["deficit", "mantenimiento", "superavit"]
ACTIVIDAD = ["sedentaria", "ligera", "moderada", "activa", "muy_activa"]
PLANTILLAS = ["general", "keto", "vegetariana", "alta_proteina"]
TIPOS_PLAN = ["menu_fijo", "menu_flexible", "intercambios"]

# Weight distribution for objectives (realistic gym distribution)
OBJ_WEIGHTS = [0.45, 0.25, 0.30]  # deficit > superavit > mantenimiento

# ── Helper functions ─────────────────────────────────────────────────────────

def random_name(sexo):
    if sexo == "M":
        nombre = random.choice(NOMBRES_M)
    else:
        nombre = random.choice(NOMBRES_F)
    ap1 = random.choice(APELLIDOS)
    ap2 = random.choice(APELLIDOS)
    return f"{nombre} {ap1} {ap2}"


def random_phone():
    return f"55{random.randint(10000000, 99999999)}"


def random_body(sexo, objetivo):
    if sexo == "M":
        peso = random.uniform(60, 110)
        estatura = random.uniform(165, 195)
        grasa = random.uniform(12, 32)
    else:
        peso = random.uniform(48, 90)
        estatura = random.uniform(150, 180)
        grasa = random.uniform(18, 38)

    if objetivo == "deficit":
        grasa = min(grasa + random.uniform(2, 8), 42)
    elif objetivo == "superavit":
        grasa = max(grasa - random.uniform(2, 5), 8)

    masa_magra = peso * (1 - grasa / 100)
    return peso, estatura, grasa, masa_magra


def random_date_in_range(start, end):
    delta = end - start
    random_days = random.uniform(0, delta.total_seconds())
    return start + timedelta(seconds=random_days)


def generate_plan_data(cliente_obj, fecha):
    peso = cliente_obj.peso_kg or 70
    estatura = cliente_obj.estatura_cm or 170
    grasa = cliente_obj.grasa_corporal_pct or 20
    actividad = cliente_obj.nivel_actividad or "moderada"
    objetivo = cliente_obj.objetivo or "mantenimiento"

    # TMB (Harris-Benedict approximation)
    if cliente_obj.sexo == "M":
        tmb = 88.362 + (13.397 * peso) + (4.799 * estatura) - (5.677 * (cliente_obj.edad or 30))
    else:
        tmb = 447.593 + (9.247 * peso) + (3.098 * estatura) - (4.330 * (cliente_obj.edad or 30))

    fact_map = {"sedentaria": 1.2, "ligera": 1.375, "moderada": 1.55, "activa": 1.725, "muy_activa": 1.9}
    factor = fact_map.get(actividad, 1.55)
    get_total = tmb * factor

    if objetivo == "deficit":
        kcal_obj = get_total * random.uniform(0.78, 0.88)
    elif objetivo == "superavit":
        kcal_obj = get_total * random.uniform(1.08, 1.18)
    else:
        kcal_obj = get_total * random.uniform(0.97, 1.03)

    kcal_real = kcal_obj * random.uniform(0.93, 1.07)

    # Macros
    prot_pct = random.uniform(0.25, 0.35)
    fat_pct = random.uniform(0.22, 0.32)
    carb_pct = 1 - prot_pct - fat_pct

    proteina_g = (kcal_real * prot_pct) / 4
    grasa_g = (kcal_real * fat_pct) / 9
    carbs_g = (kcal_real * carb_pct) / 4

    # Simulate slight weight change
    peso_momento = peso + random.uniform(-2, 2)
    grasa_momento = grasa + random.uniform(-1.5, 1.5)

    return {
        "tmb": round(tmb, 1),
        "get_total": round(get_total, 1),
        "kcal_objetivo": round(kcal_obj, 1),
        "kcal_real": round(kcal_real, 1),
        "proteina_g": round(proteina_g, 1),
        "carbs_g": round(carbs_g, 1),
        "grasa_g": round(grasa_g, 1),
        "objetivo": objetivo,
        "nivel_actividad": actividad,
        "peso_en_momento": round(peso_momento, 1),
        "grasa_en_momento": round(grasa_momento, 1),
        "desviacion_maxima_pct": round(random.uniform(3, 12), 1),
        "plantilla_tipo": cliente_obj.plantilla_tipo or "general",
        "tipo_plan": random.choice(TIPOS_PLAN),
    }


def main():
    clean = "--clean" in sys.argv

    init_db()
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()

    try:
        if clean:
            # Remove only seeded data (keep original clients)
            deleted_plans = db.query(PlanGenerado).filter(
                PlanGenerado.gym_id == GYM_ID,
                PlanGenerado.id_cliente.like("seed-%"),
            ).delete(synchronize_session=False)
            deleted_clients = db.query(Cliente).filter(
                Cliente.gym_id == GYM_ID,
                Cliente.id_cliente.like("seed-%"),
            ).delete(synchronize_session=False)
            db.commit()
            logger.info("[CLEAN] Removed %d seeded clients, %d seeded plans", deleted_clients, deleted_plans)

        # Count existing clients
        existing = db.query(Cliente).filter(
            Cliente.gym_id == GYM_ID,
            Cliente.activo == True,  # noqa: E712
        ).count()
        logger.info("[INFO] Existing active clients: %d", existing)

        # We want ~200 total active. Create the difference.
        target_clients = 200
        to_create = max(0, target_clients - existing)
        logger.info("[INFO] Will create %d new clients", to_create)

        ahora = datetime.now(timezone.utc)
        clientes_creados = []

        for i in range(to_create):
            sexo = random.choice(["M", "F"])
            objetivo = random.choices(OBJETIVOS, weights=OBJ_WEIGHTS, k=1)[0]
            nombre = random_name(sexo)
            peso, estatura, grasa, masa_magra = random_body(sexo, objetivo)

            # Distribute registration dates: 70% in last 30 days, 30% in last 90 days
            if random.random() < 0.7:
                fecha_reg = random_date_in_range(ahora - timedelta(days=30), ahora)
            else:
                fecha_reg = random_date_in_range(ahora - timedelta(days=90), ahora - timedelta(days=30))

            edad = random.randint(18, 60)
            actividad = random.choices(
                ACTIVIDAD,
                weights=[0.1, 0.2, 0.35, 0.25, 0.1],
                k=1,
            )[0]

            c = Cliente(
                id_cliente=f"seed-{uuid.uuid4().hex[:12]}",
                gym_id=GYM_ID,
                nombre=nombre,
                telefono=random_phone(),
                email=f"seed{i}@test.com",
                edad=edad,
                sexo=sexo,
                peso_kg=round(peso, 1),
                estatura_cm=round(estatura, 1),
                grasa_corporal_pct=round(grasa, 1),
                masa_magra_kg=round(masa_magra, 1),
                nivel_actividad=actividad,
                objetivo=objetivo,
                fecha_registro=fecha_reg,
                plantilla_tipo=random.choice(PLANTILLAS),
                notas=None,
                activo=True,
                total_planes_generados=0,
            )
            db.add(c)
            clientes_creados.append(c)

        db.flush()
        logger.info("[OK] Created %d clients", len(clientes_creados))

        # Now get ALL active clients for plan generation
        todos_clientes = db.query(Cliente).filter(
            Cliente.gym_id == GYM_ID,
            Cliente.activo == True,  # noqa: E712
        ).all()

        # Generate 300-500 plans distributed across clients
        # 60% of clients get 1-3 plans, 25% get 4-7 plans, 15% get 0 plans
        target_plans = random.randint(350, 450)
        planes_created = 0

        # Shuffle clients and assign plan counts
        random.shuffle(todos_clientes)
        clientes_con_plan = todos_clientes[:int(len(todos_clientes) * 0.85)]

        for c in clientes_con_plan:
            if planes_created >= target_plans:
                break

            # Determine how many plans this client gets
            r = random.random()
            if r < 0.6:
                n_plans = random.randint(1, 3)
            elif r < 0.85:
                n_plans = random.randint(4, 7)
            else:
                n_plans = random.randint(1, 2)

            n_plans = min(n_plans, target_plans - planes_created)

            for j in range(n_plans):
                # Plans distributed with bias toward recent days (more activity recently)
                if random.random() < 0.55:
                    # Last 7 days — peak activity
                    fecha_plan = random_date_in_range(ahora - timedelta(days=7), ahora)
                elif random.random() < 0.7:
                    # 7-30 days ago
                    fecha_plan = random_date_in_range(ahora - timedelta(days=30), ahora - timedelta(days=7))
                else:
                    # 30-60 days ago
                    fecha_plan = random_date_in_range(ahora - timedelta(days=60), ahora - timedelta(days=30))

                plan_data = generate_plan_data(c, fecha_plan)

                p = PlanGenerado(
                    id_cliente=c.id_cliente,
                    gym_id=GYM_ID,
                    fecha_generacion=fecha_plan,
                    tmb=plan_data["tmb"],
                    get_total=plan_data["get_total"],
                    kcal_objetivo=plan_data["kcal_objetivo"],
                    kcal_real=plan_data["kcal_real"],
                    proteina_g=plan_data["proteina_g"],
                    carbs_g=plan_data["carbs_g"],
                    grasa_g=plan_data["grasa_g"],
                    objetivo=plan_data["objetivo"],
                    nivel_actividad=plan_data["nivel_actividad"],
                    peso_en_momento=plan_data["peso_en_momento"],
                    grasa_en_momento=plan_data["grasa_en_momento"],
                    desviacion_maxima_pct=plan_data["desviacion_maxima_pct"],
                    plantilla_tipo=plan_data["plantilla_tipo"],
                    tipo_plan=plan_data["tipo_plan"],
                )
                db.add(p)
                planes_created += 1

            # Update client stats
            c.total_planes_generados = (c.total_planes_generados or 0) + n_plans
            c.ultimo_plan = max(
                [p.fecha_generacion for p in db.new if isinstance(p, PlanGenerado) and p.id_cliente == c.id_cliente],
                default=c.ultimo_plan,
            )

        db.commit()
        logger.info("[OK] Created %d plans across %d clients", planes_created, len(clientes_con_plan))

        # Final stats
        total_clients = db.query(Cliente).filter(
            Cliente.gym_id == GYM_ID,
            Cliente.activo == True,  # noqa: E712
        ).count()
        total_plans = db.query(PlanGenerado).filter(
            PlanGenerado.gym_id == GYM_ID,
        ).count()
        logger.info("[SUMMARY] Total active clients: %d, Total plans: %d", total_clients, total_plans)

    except Exception as e:
        db.rollback()
        logger.error("[ERROR] %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
