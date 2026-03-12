"""
Sistema de licenciamiento por gimnasio.

Gestiona generación, validación, renovación y desactivación de licencias
vinculadas a un UUID de instalación con hash SHA-256.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config.constantes import APP_DATA_DIR, CARPETA_CONFIG


class GestorLicencias:
    """
    Gestiona licencias de software por gimnasio.

    Cada licencia queda vinculada al UUID de instalación y firmada con
    SHA-256. El archivo ``licencia.lic`` se verifica al iniciar la app.
    """

    ARCHIVO_LICENCIA = os.path.join(APP_DATA_DIR, "licencia.lic")
    ARCHIVO_CONFIG = os.path.join(CARPETA_CONFIG, "licencia_config.json")
    SALT_MASTER: str = os.environ.get("METODO_BASE_SALT", "METODO_BASE_2026_CH")

    def __init__(self) -> None:
        self.ruta_licencia = Path(self.ARCHIVO_LICENCIA)
        self.ruta_config = Path(self.ARCHIVO_CONFIG)
        self.ruta_config.parent.mkdir(parents=True, exist_ok=True)
        if not self.ruta_config.exists():
            self._crear_config_inicial()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _crear_config_inicial(self) -> None:
        config = {
            "id_instalacion": str(uuid.uuid4()),
            "fecha_primera_instalacion": datetime.now().isoformat(),
            "version": "1.0.0",
        }
        with open(self.ruta_config, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def _obtener_id_instalacion(self) -> str:
        try:
            with open(self.ruta_config, "r", encoding="utf-8") as f:
                return json.load(f).get("id_instalacion", "")
        except (json.JSONDecodeError, OSError):
            self._crear_config_inicial()
            with open(self.ruta_config, "r", encoding="utf-8") as f:
                return json.load(f)["id_instalacion"]

    def _generar_hash(self, nombre_gym: str, id_instalacion: str,
                      fecha_expiracion: str) -> str:
        datos = f"{nombre_gym}|{id_instalacion}|{fecha_expiracion}|{self.SALT_MASTER}"
        return hashlib.sha256(datos.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generar_licencia_gym(
        self,
        nombre_gym: str,
        duracion_dias: int = 365,
        email_contacto: str = "",
        telefono_contacto: str = "",
        id_instalacion_cliente: str = None,
    ) -> str:
        """Genera una nueva licencia para *nombre_gym* y la guarda en disco."""
        if not nombre_gym or not nombre_gym.strip():
            raise ValueError("El nombre del gimnasio no puede estar vacío")
        if duracion_dias <= 0:
            raise ValueError("La duración debe ser mayor a 0 días")

        id_instalacion = id_instalacion_cliente or self._obtener_id_instalacion()
        fecha_emision = datetime.now()
        fecha_expiracion = fecha_emision + timedelta(days=duracion_dias)

        hash_licencia = self._generar_hash(
            nombre_gym, id_instalacion, fecha_expiracion.strftime("%Y-%m-%d"),
        )

        licencia = {
            "nombre_gym": nombre_gym.strip(),
            "id_instalacion": id_instalacion,
            "clave": hash_licencia,
            "fecha_emision": fecha_emision.isoformat(),
            "fecha_expiracion": fecha_expiracion.isoformat(),
            "duracion_dias": duracion_dias,
            "email_contacto": email_contacto,
            "telefono_contacto": telefono_contacto,
            "version_software": "1.0.0",
            "activa": True,
        }

        with open(self.ruta_licencia, "w", encoding="utf-8") as f:
            json.dump(licencia, f, indent=2, ensure_ascii=False)

        return hash_licencia

    def validar_licencia(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Valida la licencia actual.

        Returns:
            ``(es_valida, mensaje, datos_licencia | None)``
        """
        if not self.ruta_licencia.exists():
            return False, "No se encontró archivo de licencia. Contacta a soporte.", None

        try:
            with open(self.ruta_licencia, "r", encoding="utf-8") as f:
                lic = json.load(f)
        except json.JSONDecodeError:
            return False, "Licencia corrupta: formato JSON inválido.", None
        except OSError as exc:
            return False, f"Error leyendo licencia: {exc}", None

        for campo in ("nombre_gym", "id_instalacion", "clave", "fecha_expiracion", "activa"):
            if campo not in lic:
                return False, f"Licencia corrupta: falta campo '{campo}'", None

        if not lic.get("activa", False):
            return False, "Licencia desactivada. Contacta a soporte.", None

        if lic["id_instalacion"] != self._obtener_id_instalacion():
            return False, "Licencia inválida: ID de instalación no coincide.", None

        fecha_exp_str = lic["fecha_expiracion"].split("T")[0]
        hash_esperado = self._generar_hash(
            lic["nombre_gym"], lic["id_instalacion"], fecha_exp_str,
        )
        if lic["clave"] != hash_esperado:
            return False, "Licencia inválida: hash de seguridad no coincide.", None

        fecha_exp = datetime.fromisoformat(lic["fecha_expiracion"])
        ahora = datetime.now()
        if ahora > fecha_exp:
            dias = (ahora - fecha_exp).days
            return False, f"Licencia expirada hace {dias} días. Renueva tu licencia.", None

        dias_rest = (fecha_exp - ahora).days
        if dias_rest <= 30:
            return True, f"⚠️ Licencia válida — expira en {dias_rest} días", lic
        return True, f"✅ Licencia válida ({dias_rest} días restantes)", lic

    def renovar_licencia(self, duracion_dias: int = 365) -> Tuple[bool, str]:
        """Extiende la licencia actual por *duracion_dias*."""
        _, _, lic = self.validar_licencia()
        if not lic:
            return False, "No hay licencia existente para renovar"

        fecha_exp = datetime.fromisoformat(lic["fecha_expiracion"])
        base = max(datetime.now(), fecha_exp)
        nueva_exp = base + timedelta(days=duracion_dias)

        nuevo_hash = self._generar_hash(
            lic["nombre_gym"], lic["id_instalacion"], nueva_exp.strftime("%Y-%m-%d"),
        )
        lic["clave"] = nuevo_hash
        lic["fecha_expiracion"] = nueva_exp.isoformat()
        lic["fecha_renovacion"] = datetime.now().isoformat()
        lic["activa"] = True

        with open(self.ruta_licencia, "w", encoding="utf-8") as f:
            json.dump(lic, f, indent=2, ensure_ascii=False)
        return True, f"Licencia renovada hasta {nueva_exp.strftime('%Y-%m-%d')}"

    def desactivar_licencia(self) -> Tuple[bool, str]:
        """Desactiva la licencia (transferencia / revocación)."""
        try:
            with open(self.ruta_licencia, "r", encoding="utf-8") as f:
                lic = json.load(f)
            lic["activa"] = False
            lic["fecha_desactivacion"] = datetime.now().isoformat()
            with open(self.ruta_licencia, "w", encoding="utf-8") as f:
                json.dump(lic, f, indent=2, ensure_ascii=False)
            return True, "Licencia desactivada exitosamente"
        except Exception as exc:
            return False, f"Error desactivando licencia: {exc}"

    def obtener_info_licencia(self) -> Optional[Dict]:
        """Devuelve los datos crudos de la licencia, o ``None``."""
        if not self.ruta_licencia.exists():
            return None
        try:
            with open(self.ruta_licencia, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None


# ────────────────────────────────────────────────────────────────────
# CLI para generar licencias (python -m core.licencia)
# ────────────────────────────────────────────────────────────────────

def generar_licencia_cli() -> None:
    print("=" * 60)
    print("GENERADOR DE LICENCIAS — MÉTODO BASE")
    print("Consultoría Hernández")
    print("=" * 60)
    print()

    gestor = GestorLicencias()

    nombre_gym = input("📋 Nombre del gimnasio: ").strip()
    if not nombre_gym:
        print("❌ Error: El nombre no puede estar vacío")
        return

    print("\n🔐 ¿La licencia es para esta computadora (1) o para la PC de un cliente (2)?")
    destino = input("Selecciona opción [1-2]: ").strip()
    id_instalacion_cliente = None
    if destino == "2":
        id_instalacion_cliente = input("🆔 ID de instalación del cliente: ").strip()
        if not id_instalacion_cliente:
            print("❌ Error: El ID de instalación no puede estar vacío")
            return
    elif destino != "1":
        print("❌ Opción inválida")
        return

    email = input("📧 Email de contacto (opcional): ").strip()
    telefono = input("📱 Teléfono de contacto (opcional): ").strip()

    print("\n⏱️  Duración de la licencia:")
    print("  1. 30 días  (demo)")
    print("  2. 365 días (1 año)")
    print("  3. 730 días (2 años)")
    print("  4. Personalizado")

    opcion = input("\nSelecciona opción [1-4]: ").strip()
    dur_map = {"1": 30, "2": 365, "3": 730}

    if opcion in dur_map:
        duracion = dur_map[opcion]
    elif opcion == "4":
        try:
            duracion = int(input("Ingresa días de validez: "))
        except ValueError:
            print("❌ Número inválido"); return
    else:
        print("❌ Opción inválida"); return

    try:
        clave = gestor.generar_licencia_gym(
            nombre_gym=nombre_gym, duracion_dias=duracion,
            email_contacto=email, telefono_contacto=telefono,
            id_instalacion_cliente=id_instalacion_cliente,
        )
        fecha_exp = (datetime.now() + timedelta(days=duracion)).strftime("%Y-%m-%d")
        print("\n" + "=" * 60)
        print("✅ LICENCIA GENERADA EXITOSAMENTE")
        print("=" * 60)
        print(f"  🏋️  Gimnasio : {nombre_gym}")
        print(f"  🔑 Clave    : {clave[:16]}…{clave[-16:]}")
        print(f"  📅 Expira   : {fecha_exp}")
        print(f"  📁 Archivo  : {gestor.ruta_licencia.absolute()}")
        print("=" * 60)
    except Exception as exc:
        print(f"\n❌ Error generando licencia: {exc}")


if __name__ == "__main__":
    generar_licencia_cli()
