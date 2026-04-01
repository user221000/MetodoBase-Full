"""
src/repositories — Repository Pattern para abstracción de BD.

Implementa el patrón Strangler Fig para migración gradual de legacy → SQLAlchemy.

Módulos:
- base.py: Interface base y tipos
- cliente_repository.py: Repositorio de clientes
- plan_repository.py: Repositorio de planes
- sync_service.py: Sincronización entre BDs

Uso:
    from src.repositories import ClienteRepository, get_cliente_repo
    
    repo = get_cliente_repo()
    cliente = repo.get_by_id("uuid-xxx")
    repo.save(cliente)
"""
from .base import (
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    SyncError,
    BaseRepository,
)
from .cliente_repository import ClienteRepository, get_cliente_repo
from .plan_repository import PlanRepository, get_plan_repo

__all__ = [
    # Errors
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "SyncError",
    # Base
    "BaseRepository",
    # Repositories
    "ClienteRepository",
    "PlanRepository",
    # Factories
    "get_cliente_repo",
    "get_plan_repo",
]
