# backend/app/infrastructure/repositories.py
"""
Repositorio genérico para operaciones CRUD con SQLAlchemy async.

Proporciona una capa de abstracción sobre la sesión de base de datos
con manejo de errores, logging y operaciones optimizadas.
"""

import logging
from typing import Any, Generic, Optional, Sequence, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Base

logger = logging.getLogger(__name__)

# TypeVar bound a Base de models.py (única fuente de verdad)
T = TypeVar("T", bound=Base)


# ----------------- EXCEPTIONS -----------------


class RepositoryError(Exception):
    """Error base para operaciones de repositorio."""
    pass


class NotFoundError(RepositoryError):
    """Entidad no encontrada."""
    pass


class IntegrityConstraintError(RepositoryError):
    """Violación de restricción de integridad (FK, unique, etc.)."""
    pass


# ----------------- REPOSITORY -----------------


class BaseRepository(Generic[T]):
    """
    Repositorio genérico para modelos SQLAlchemy async.
    
    Características:
    - Operaciones CRUD con manejo de errores
    - Soporte para cualquier clave primaria (no asume 'id')
    - Logging de operaciones
    - Métodos optimizados para bulk operations
    
    Uso:
        async with AsyncSessionLocal() as session:
            repo = BaseRepository(User, session)
            user = await repo.add(User(email="test@example.com"))
            user = await repo.get_by_id(1)
    """

    __slots__ = ("model", "session", "_pk_name")

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        """
        Inicializa el repositorio.
        
        Args:
            model: Clase del modelo SQLAlchemy
            session: Sesión async de SQLAlchemy
        """
        self.model = model
        self.session = session
        # Detectar nombre de la clave primaria dinámicamente
        self._pk_name = self._get_primary_key_name()

    def _get_primary_key_name(self) -> str:
        """Obtiene el nombre de la columna de clave primaria."""
        mapper = inspect(self.model)
        pk_columns = mapper.primary_key
        if len(pk_columns) != 1:
            logger.warning(f"{self.model.__name__} tiene clave primaria compuesta, usando 'id'")
            return "id"
        return pk_columns[0].name

    async def get_all(self, limit: Optional[int] = None) -> Sequence[T]:
        """
        Obtiene todos los registros del modelo.
        
        Args:
            limit: Límite opcional de registros
            
        Returns:
            Secuencia de entidades
        """
        try:
            stmt = select(self.model)
            if limit:
                stmt = stmt.limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error en get_all({self.model.__name__}): {e}")
            raise RepositoryError(f"Error al obtener registros: {e}") from e

    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Obtiene una entidad por su clave primaria.
        
        Args:
            entity_id: Valor de la clave primaria
            
        Returns:
            Entidad o None si no existe
        """
        try:
            pk_column = getattr(self.model, self._pk_name)
            stmt = select(self.model).where(pk_column == entity_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error en get_by_id({self.model.__name__}, {entity_id}): {e}")
            raise RepositoryError(f"Error al obtener entidad: {e}") from e

    async def add(self, obj: T) -> T:
        """
        Agrega una nueva entidad.
        
        Args:
            obj: Entidad a agregar
            
        Returns:
            Entidad con ID asignado
            
        Raises:
            IntegrityConstraintError: Si viola restricciones de integridad
        """
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            logger.debug(f"Creado {self.model.__name__} con {self._pk_name}={getattr(obj, self._pk_name)}")
            return obj
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"IntegrityError en add({self.model.__name__}): {e}")
            raise IntegrityConstraintError(f"Violación de integridad: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error en add({self.model.__name__}): {e}")
            raise RepositoryError(f"Error al crear entidad: {e}") from e

    async def update(self, obj: T, **kwargs: Any) -> T:
        """
        Actualiza una entidad existente.
        
        Args:
            obj: Entidad a actualizar (debe estar en sesión o tener PK)
            **kwargs: Campos a actualizar
            
        Returns:
            Entidad actualizada
            
        Raises:
            RepositoryError: Si falla la actualización
        """
        try:
            # Validar que los campos existen en el modelo
            valid_columns = {c.key for c in inspect(self.model).mapper.column_attrs}
            invalid_keys = set(kwargs.keys()) - valid_columns
            if invalid_keys:
                raise ValueError(f"Campos inválidos para {self.model.__name__}: {invalid_keys}")
            
            for key, value in kwargs.items():
                setattr(obj, key, value)
            
            # merge() es más seguro que add() para objetos potencialmente desvinculados
            merged = await self.session.merge(obj)
            await self.session.commit()
            await self.session.refresh(merged)
            logger.debug(f"Actualizado {self.model.__name__} con {self._pk_name}={getattr(merged, self._pk_name)}")
            return merged
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"IntegrityError en update({self.model.__name__}): {e}")
            raise IntegrityConstraintError(f"Violación de integridad: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error en update({self.model.__name__}): {e}")
            raise RepositoryError(f"Error al actualizar entidad: {e}") from e

    async def delete(self, obj: T) -> None:
        """
        Elimina una entidad.
        
        Args:
            obj: Entidad a eliminar
        """
        try:
            await self.session.delete(obj)
            await self.session.commit()
            logger.debug(f"Eliminado {self.model.__name__}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error en delete({self.model.__name__}): {e}")
            raise RepositoryError(f"Error al eliminar entidad: {e}") from e

    async def delete_by_id(self, entity_id: Any) -> bool:
        """
        Elimina una entidad por su clave primaria.
        
        Args:
            entity_id: Valor de la clave primaria
            
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            pk_column = getattr(self.model, self._pk_name)
            stmt = sa_delete(self.model).where(pk_column == entity_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Eliminado {self.model.__name__} con {self._pk_name}={entity_id}")
            return deleted
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error en delete_by_id({self.model.__name__}, {entity_id}): {e}")
            raise RepositoryError(f"Error al eliminar entidad: {e}") from e

    async def bulk_add(self, objs: list[T], refresh: bool = False) -> list[T]:
        """
        Agrega múltiples entidades de forma eficiente.
        
        Args:
            objs: Lista de entidades a agregar
            refresh: Si True, refresca cada objeto (N+1 queries, usar con cuidado)
            
        Returns:
            Lista de entidades (con IDs si refresh=True o si son autoincrementales)
            
        Note:
            Por defecto refresh=False para evitar N+1 queries.
            SQLAlchemy asigna IDs autoincrementales después del commit sin refresh.
        """
        if not objs:
            return []
        
        try:
            self.session.add_all(objs)
            await self.session.commit()
            
            # Solo refrescar si es explícitamente solicitado
            if refresh:
                for obj in objs:
                    await self.session.refresh(obj)
            
            logger.debug(f"Bulk add: {len(objs)} {self.model.__name__}")
            return objs
        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"IntegrityError en bulk_add({self.model.__name__}): {e}")
            raise IntegrityConstraintError(f"Violación de integridad en bulk: {e}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error en bulk_add({self.model.__name__}): {e}")
            raise RepositoryError(f"Error en inserción masiva: {e}") from e

    async def exists(self, entity_id: Any) -> bool:
        """
        Verifica si existe una entidad con el ID dado.
        
        Args:
            entity_id: Valor de la clave primaria
            
        Returns:
            True si existe, False si no
        """
        return await self.get_by_id(entity_id) is not None

    async def count(self) -> int:
        """
        Cuenta el total de registros.
        
        Returns:
            Número de registros
        """
        from sqlalchemy import func
        try:
            stmt = select(func.count()).select_from(self.model)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error en count({self.model.__name__}): {e}")
            raise RepositoryError(f"Error al contar registros: {e}") from e

