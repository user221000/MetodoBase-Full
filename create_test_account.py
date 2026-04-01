#!/usr/bin/env python3
"""
create_test_account.py — Crea una cuenta de prueba con 200 clientes realistas.

Uso:
    python create_test_account.py
    python create_test_account.py --email test@gym.com --password test123
"""
import argparse
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Inicializar auth y database
from web.auth import init_auth, crear_usuario
from web.database.engine import init_db, get_engine
from web.database.models import Cliente, GymProfile
from sqlalchemy.orm import sessionmaker

# Data pools
NOMBRES_M = [
    "Carlos", "Miguel", "José", "Luis", "Juan", "Fernando", "Ricardo", "Eduardo",
    "Andrés", "Diego", "Alejandro", "Daniel", "Pedro", "Roberto", "Sergio",
    "Pablo", "Javier", "Rafael", "Óscar", "Arturo", "Gabriel", "Iván",
    "Héctor", "Manuel", "Raúl", "Enrique", "Francisco", "Alberto", "Hugo",
    "Mario", "Gustavo", "Emilio", "Adrián", "Víctor", "Ignacio", "Samuel",
]

NOMBRES_F = [
    "María", "Ana", "Sofía", "Laura", "Carmen", "Valentina", "Lucía", "Paula",
    "Andrea", "Daniela", "Gabriela", "Isabella", "Mariana", "Fernanda", "Karen",
    "Diana", "Patricia", "Claudia", "Rosa", "Mónica", "Elena", "Alejandra",
    "Natalia", "Camila", "Verónica", "Paola", "Sandra", "Teresa", "Liliana",
    "Karla", "Jimena", "Regina", "Julieta", "Silvia", "Estefanía", "Valeria",
]

APELLIDOS = [
    "García", "Hernández", "Martínez", "López", "González", "Rodríguez",
    "Pérez", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Jiménez", "Ruiz", "Castillo",
    "Vega", "Delgado", "Ávila", "Guerrero", "Contreras", "Figueroa",
    "Salazar", "Mejía", "Cortés", "Fuentes", "Navarro", "Acosta",
]

from config.constantes import NIVELES_ACTIVIDAD
ACTIVIDAD = sorted(NIVELES_ACTIVIDAD)
OBJETIVOS = ["deficit", "mantenimiento", "superavit"]
PLANTILLAS = ["general", "keto", "vegetariana", "alta_proteina"]


def random_name(sexo: str) -> str:
    """Genera nombre completo aleatorio."""
    pool = NOMBRES_M if sexo == "M" else NOMBRES_F
    nombre = random.choice(pool)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    return f"{nombre} {apellido1} {apellido2}"


def random_phone() -> str:
    """Genera teléfono mexicano aleatorio."""
    return f"521{random.randint(3000000000, 9999999999)}"


def random_body(sexo: str, objetivo: str) -> tuple[float, float, float, float]:
    """Genera medidas corporales realistas según sexo y objetivo."""
    if sexo == "M":
        if objetivo == "deficit":
            peso = random.uniform(85, 110)
            grasa = random.uniform(22, 32)
        elif objetivo == "superavit":
            peso = random.uniform(60, 75)
            grasa = random.uniform(8, 15)
        else:
            peso = random.uniform(70, 85)
            grasa = random.uniform(15, 22)
        estatura = random.uniform(165, 185)
    else:
        if objetivo == "deficit":
            peso = random.uniform(70, 90)
            grasa = random.uniform(28, 38)
        elif objetivo == "superavit":
            peso = random.uniform(48, 60)
            grasa = random.uniform(15, 22)
        else:
            peso = random.uniform(55, 70)
            grasa = random.uniform(22, 28)
        estatura = random.uniform(155, 172)

    masa_magra = peso * (1 - grasa / 100)
    return peso, estatura, grasa, masa_magra


def random_date_in_range(start: datetime, end: datetime) -> datetime:
    """Genera fecha aleatoria en un rango."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def main():
    parser = argparse.ArgumentParser(description="Crear cuenta de prueba con 200 clientes")
    parser.add_argument("--email", default="test@gym.com", help="Email del gym")
    parser.add_argument("--password", default="test123456", help="Password del gym")
    parser.add_argument("--nombre", default="Gym Test", help="Nombre del gym")
    parser.add_argument("--clientes", type=int, default=200, help="Número de clientes a crear")
    args = parser.parse_args()

    print("\n🏋️  Creando cuenta de prueba MetodoBase")
    print("=" * 60)

    # Initialize systems
    init_auth()
    init_db()

    # Helper para sincronizar user auth → SQLAlchemy
    def sync_user_to_sa(usuario: dict, db_session):
        """Upsert: copia el usuario de auth a la tabla SA si no existe."""
        from web.database.models import Usuario, UserRole
        
        exists = db_session.query(Usuario.id).filter_by(id=usuario["id"]).first()
        if not exists:
            role_str = usuario.get("role")
            if role_str:
                try:
                    role = UserRole(role_str)
                except ValueError:
                    role = UserRole.OWNER if usuario.get("tipo") == "gym" else UserRole.VIEWER
            else:
                role = UserRole.OWNER if usuario.get("tipo") == "gym" else UserRole.VIEWER
            
            sa_user = Usuario(
                id=usuario["id"],
                email=usuario.get("email", ""),
                password_hash=usuario.get("password_hash", "synced"),
                nombre=usuario.get("nombre", ""),
                apellido=usuario.get("apellido", ""),
                tipo=usuario.get("tipo", "usuario"),
                role=role,
                team_gym_id=usuario.get("team_gym_id"),
            )
            db_session.add(sa_user)
            print(f"   ✅ Usuario sincronizado a SQLAlchemy")

    # 1. Crear gym/usuario principal
    print(f"\n1️⃣  Creando gym: {args.email}")
    try:
        usuario = crear_usuario(
            email=args.email,
            password=args.password,
            nombre=args.nombre,
            apellido="",
            tipo="gym"
        )
        gym_id = usuario["id"]
        print(f"   ✅ Gym creado con ID: {gym_id}")
    except ValueError as e:
        error_msg = str(e)
        if "ya está registrado" in error_msg or "ya existe" in error_msg:
            # Gym ya existe, intentar verificar credenciales
            from web.auth import verificar_credenciales
            usuario = verificar_credenciales(args.email, args.password)
            if not usuario:
                print(f"   ❌ El gym ya existe pero la contraseña es incorrecta.")
                print(f"   💡 Usa la contraseña correcta o un email diferente.")
                return
            gym_id = usuario["id"]
            print(f"   ⚠️  Gym ya existe, usando ID: {gym_id}")
        else:
            print(f"   ❌ Error: {e}")
            return

    # 2. Crear GymProfile
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Sincronizar usuario a SQLAlchemy primero
        sync_user_to_sa(usuario, db)
        db.commit()
        
        existing_profile = db.query(GymProfile).filter_by(gym_id=gym_id).first()
        if not existing_profile:
            gym_profile = GymProfile(
                gym_id=gym_id,
                nombre_negocio=args.nombre,
                telefono=random_phone(),
                direccion="Calle Test 123, Colonia Fitness",
                ciudad="Ciudad de México",
                estado="CDMX",
                pais="México",
                codigo_postal_fiscal="01000",
            )
            db.add(gym_profile)
            db.commit()
            print("   ✅ GymProfile creado")
        else:
            print("   ⚠️  GymProfile ya existe")

        # 3. Crear clientes
        print(f"\n2️⃣  Creando {args.clientes} clientes con datos realistas...")
        
        # Verificar cuántos ya existen
        existing = db.query(Cliente).filter(
            Cliente.gym_id == gym_id,
            Cliente.activo == True
        ).count()
        
        to_create = args.clientes - existing
        if to_create <= 0:
            print(f"   ⚠️  Ya existen {existing} clientes activos. No se crearán más.")
            print(f"\n✅ Cuenta de prueba lista:")
            print(f"   📧 Email: {args.email}")
            print(f"   🔑 Password: {args.password}")
            print(f"   👥 Clientes: {existing}")
            print(f"   🔗 Login: http://127.0.0.1:8088/login-gym\n")
            return

        print(f"   📊 Clientes existentes: {existing}")
        print(f"   ➕ Nuevos a crear: {to_create}")

        ahora = datetime.now(timezone.utc)
        obj_weights = [0.45, 0.25, 0.30]  # deficit > mantenimiento > superavit
        act_weights = [0.15, 0.25, 0.40, 0.20]  # nula, leve, moderada, intensa

        created = 0
        for i in range(to_create):
            sexo = random.choice(["M", "F"])
            objetivo = random.choices(OBJETIVOS, weights=obj_weights, k=1)[0]
            nombre = random_name(sexo)
            peso, estatura, grasa, masa_magra = random_body(sexo, objetivo)

            # Distribución temporal: 70% últimos 30 días, 30% últimos 90 días
            if random.random() < 0.7:
                fecha_reg = random_date_in_range(ahora - timedelta(days=30), ahora)
            else:
                fecha_reg = random_date_in_range(ahora - timedelta(days=90), ahora - timedelta(days=30))

            edad = random.randint(18, 65)
            actividad = random.choices(ACTIVIDAD, weights=act_weights, k=1)[0]

            cliente = Cliente(
                id_cliente=f"test-{uuid.uuid4().hex[:12]}",
                gym_id=gym_id,
                nombre=nombre,
                telefono=random_phone(),
                email=f"cliente{existing + i + 1}@test.com",
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
            db.add(cliente)
            created += 1

            if (created) % 50 == 0:
                db.flush()
                print(f"   ✓ {created}/{to_create} clientes creados...")

        db.commit()
        print(f"   ✅ {created} clientes nuevos creados")

        # Stats finales
        total_clientes = db.query(Cliente).filter(
            Cliente.gym_id == gym_id,
            Cliente.activo == True
        ).count()

        print("\n" + "=" * 60)
        print("✅ Cuenta de prueba creada exitosamente")
        print("=" * 60)
        print(f"📧 Email:    {args.email}")
        print(f"🔑 Password: {args.password}")
        print(f"🆔 Gym ID:   {gym_id}")
        print(f"👥 Clientes: {total_clientes} activos")
        print(f"\n🔗 Login:    http://127.0.0.1:8088/login-gym")
        print("=" * 60 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
