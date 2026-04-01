"""
src/compat/gestor_bd_compat.py — Capa de compatibilidad legacy → Repository.

FASE 7 del plan de consolidación de BD.

Esta capa permite que el código legacy que usa GestorBDClientes
funcione sin cambios, delegando internamente al nuevo Repository.

Uso:
    # Código legacy (sin cambios):
    from src.gestor_bd import GestorBDClientes
    gestor = GestorBDClientes()
    gestor.guardar_cliente(data)
    
    # Internamente usa Repository via este compat layer

Patrón:
    GestorBDClientes (legacy interface)
         ↓
    GestorBDCompat (this file)
         ↓
    ClienteRepository (nuevo sistema)
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.feature_flags import get_migration_flags

logger = logging.getLogger(__name__)


class GestorBDCompat:
    """
    Wrapper de compatibilidad que implementa la interfaz de GestorBDClientes
    pero usa internamente el nuevo Repository pattern.
    
    Permite migración gradual sin romper código existente.
    """
    
    def __init__(self, db_path: str = "clientes.db"):
        self._db_path = db_path
        self._flags = get_migration_flags()
        self._cliente_repo = None
        self._plan_repo = None
    
    @property
    def cliente_repo(self):
        """Lazy load ClienteRepository."""
        if self._cliente_repo is None:
            from src.repositories.cliente_repository import ClienteRepository
            self._cliente_repo = ClienteRepository(
                legacy_db_path=self._db_path,
                flags=self._flags,
            )
        return self._cliente_repo
    
    @property
    def plan_repo(self):
        """Lazy load PlanRepository."""
        if self._plan_repo is None:
            from src.repositories.plan_repository import PlanRepository
            self._plan_repo = PlanRepository(
                legacy_db_path=self._db_path,
                flags=self._flags,
            )
        return self._plan_repo
    
    # ══════════════════════════════════════════════════════════════════════════
    # CLIENTES - Métodos que espera el código legacy
    # ══════════════════════════════════════════════════════════════════════════
    
    def guardar_cliente(
        self,
        id_cliente: str,
        nombre: str,
        edad: Optional[int] = None,
        sexo: str = "M",
        peso_kg: Optional[float] = None,
        estatura_cm: Optional[float] = None,
        grasa_corporal_pct: Optional[float] = None,
        masa_magra_kg: Optional[float] = None,
        nivel_actividad: str = "moderado",
        objetivo: str = "mantener",
        plantilla_tipo: str = "general",
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> bool:
        """
        Guarda cliente. Compatible con firma de GestorBDClientes.
        """
        from src.repositories.base import ClienteDTO
        
        try:
            dto = ClienteDTO(
                id_cliente=id_cliente,
                nombre=nombre,
                edad=edad,
                sexo=sexo,
                peso_kg=peso_kg,
                estatura_cm=estatura_cm,
                grasa_corporal_pct=grasa_corporal_pct,
                masa_magra_kg=masa_magra_kg,
                nivel_actividad=nivel_actividad,
                objetivo=objetivo,
                plantilla_tipo=plantilla_tipo,
                telefono=telefono,
                email=email,
                notas=notas,
                fecha_registro=datetime.now(),
            )
            
            self.cliente_repo.save(dto)
            return True
            
        except Exception as e:
            logger.error("Error guardando cliente %s: %s", id_cliente, e)
            return False
    
    def obtener_cliente(self, id_cliente: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene cliente por ID. Retorna dict para compatibilidad.
        """
        dto = self.cliente_repo.get_by_id(id_cliente)
        if dto:
            return dto.to_dict()
        return None
    
    def listar_clientes(
        self,
        limite: int = 100,
        offset: int = 0,
        activo: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lista clientes. Retorna lista de dicts.
        """
        filters = {}
        if activo is not None:
            filters["activo"] = activo
        
        dtos = self.cliente_repo.get_all(
            offset=offset,
            limit=limite,
            filters=filters if filters else None,
        )
        return [dto.to_dict() for dto in dtos]
    
    def buscar_clientes(self, nombre: str, limite: int = 50) -> List[Dict[str, Any]]:
        """
        Busca clientes por nombre.
        """
        dtos = self.cliente_repo.search_by_name(nombre, limit=limite)
        return [dto.to_dict() for dto in dtos]
    
    def actualizar_cliente(self, id_cliente: str, **campos) -> bool:
        """
        Actualiza campos específicos de un cliente.
        """
        from src.repositories.base import ClienteDTO
        
        try:
            existing = self.cliente_repo.get_by_id(id_cliente)
            if not existing:
                logger.warning("Cliente %s no encontrado para actualizar", id_cliente)
                return False
            
            # Actualizar campos
            data = existing.to_dict()
            data.update(campos)
            
            dto = ClienteDTO.from_dict(data)
            self.cliente_repo.save(dto)
            return True
            
        except Exception as e:
            logger.error("Error actualizando cliente %s: %s", id_cliente, e)
            return False
    
    def eliminar_cliente(self, id_cliente: str) -> bool:
        """
        Elimina cliente (soft delete).
        """
        return self.cliente_repo.delete(id_cliente)
    
    def cliente_existe(self, id_cliente: str) -> bool:
        """
        Verifica si cliente existe.
        """
        return self.cliente_repo.exists(id_cliente)
    
    def contar_clientes(self, activo: Optional[bool] = None) -> int:
        """
        Cuenta clientes.
        """
        filters = {"activo": activo} if activo is not None else None
        return self.cliente_repo.count(filters=filters)
    
    # ══════════════════════════════════════════════════════════════════════════
    # PLANES GENERADOS
    # ══════════════════════════════════════════════════════════════════════════
    
    def guardar_plan(
        self,
        id_cliente: str,
        tmb: float,
        get_total: float,
        kcal_objetivo: float,
        kcal_real: float,
        proteina_g: float,
        carbs_g: float,
        grasa_g: float,
        objetivo: str = "mantener",
        nivel_actividad: str = "moderado",
        plantilla_tipo: str = "general",
        tipo_plan: str = "menu_fijo",
        ruta_pdf: Optional[str] = None,
        desviacion_maxima_pct: Optional[float] = None,
        peso_en_momento: Optional[float] = None,
        grasa_en_momento: Optional[float] = None,
    ) -> Optional[int]:
        """
        Guarda plan generado. Retorna ID del plan.
        """
        from src.repositories.base import PlanDTO
        
        try:
            dto = PlanDTO(
                id_cliente=id_cliente,
                fecha_generacion=datetime.now(),
                tmb=tmb,
                get_total=get_total,
                kcal_objetivo=kcal_objetivo,
                kcal_real=kcal_real,
                proteina_g=proteina_g,
                carbs_g=carbs_g,
                grasa_g=grasa_g,
                objetivo=objetivo,
                nivel_actividad=nivel_actividad,
                plantilla_tipo=plantilla_tipo,
                tipo_plan=tipo_plan,
                ruta_pdf=ruta_pdf,
                desviacion_maxima_pct=desviacion_maxima_pct,
                peso_en_momento=peso_en_momento,
                grasa_en_momento=grasa_en_momento,
            )
            
            saved = self.plan_repo.save(dto)
            return saved.id
            
        except Exception as e:
            logger.error("Error guardando plan para %s: %s", id_cliente, e)
            return None
    
    def obtener_planes_cliente(
        self,
        id_cliente: str,
        limite: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene planes de un cliente.
        """
        dtos = self.plan_repo.get_by_cliente(id_cliente, limit=limite)
        return [dto.to_dict() for dto in dtos]
    
    def obtener_ultimo_plan(self, id_cliente: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último plan de un cliente.
        """
        planes = self.obtener_planes_cliente(id_cliente, limite=1)
        return planes[0] if planes else None
    
    def contar_planes_cliente(self, id_cliente: str) -> int:
        """
        Cuenta planes de un cliente.
        """
        return len(self.plan_repo.get_by_cliente(id_cliente, limit=10000))
    
    # ══════════════════════════════════════════════════════════════════════════
    # ESTADÍSTICAS (mantiene interfaz legacy)
    # ══════════════════════════════════════════════════════════════════════════
    
    def obtener_estadisticas_gym(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del gym.
        """
        return {
            "total_clientes": self.contar_clientes(),
            "clientes_activos": self.contar_clientes(activo=True),
            "total_planes": self.plan_repo.count(),
        }
    
    def registrar_estadistica_diaria(self) -> bool:
        """
        Registra estadística del día.
        
        TODO: Implementar cuando se migre tabla estadisticas_gym.
        """
        logger.info("registrar_estadistica_diaria: pendiente de implementar")
        return True


# ── Factory Function ────────────────────────────────────────────────────────

_compat_instance: Optional[GestorBDCompat] = None


def get_gestor_compat(db_path: str = "clientes.db") -> GestorBDCompat:
    """
    Obtiene instancia singleton de GestorBDCompat.
    
    Uso cuando se quiera usar el nuevo sistema gradualmente:
    
        from src.compat.gestor_bd_compat import get_gestor_compat
        gestor = get_gestor_compat()
        gestor.guardar_cliente(...)
    """
    global _compat_instance
    if _compat_instance is None:
        _compat_instance = GestorBDCompat(db_path)
    return _compat_instance
