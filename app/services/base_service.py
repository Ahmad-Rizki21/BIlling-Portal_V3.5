"""
Base Service Layer untuk menghilangkan duplikasi kode CRUD operations
"""

from typing import TypeVar, Type, Generic, List, Optional, Dict, Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

# Type variables untuk generics
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class untuk CRUD operations yang umum digunakan.
    Menghilangkan duplikasi kode di seluruh router files.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        self.model_name = model.__name__.lower()

    async def get_by_id(self, id: int) -> ModelType:
        """Mengambil single record by ID dengan error handling standar"""
        result = await self.db.get(self.model, id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.model.__name__} tidak ditemukan")
        return result

    async def get_by_id_with_relations(self, id: int, relations: Optional[List[str]] = None) -> ModelType:
        """Mengambil record by ID dengan eager loading untuk relasi tertentu"""
        query = select(self.model).where(self.model.id == id)  # type: ignore

        # Add eager loading untuk relasi jika ditentukan
        if relations is not None:
            for relation in relations:
                if hasattr(self.model, relation):
                    query = query.options(joinedload(getattr(self.model, relation)))

        result = (await self.db.execute(query)).scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.model.__name__} tidak ditemukan")
        return result

    async def get_all(
        self,
        skip: int = 0,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by_field: str = "id",
        order_desc: bool = True,
    ) -> Sequence[ModelType]:
        """Mengambil semua records dengan pagination, search, dan ordering"""

        query = select(self.model)

        # Add search filter jika search term dan search fields disediakan
        if search and search_fields is not None:
            search_term = f"%{search}%"
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(getattr(self.model, field).ilike(search_term))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Add ordering
        if hasattr(self.model, order_by_field):
            order_column = getattr(self.model, order_by_field)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Add pagination
        if limit is not None:
            query = query.offset(skip).limit(limit)

        return (await self.db.execute(query)).scalars().all()

    async def get_total_count(self, search: Optional[str] = None, search_fields: Optional[List[str]] = None) -> int:
        """Menghitung total records dengan filter yang sama seperti get_all"""
        query = select(func.count(self.model.id))  # type: ignore

        # Add search filter jika search term dan search fields disediakan
        if search and search_fields is not None:
            search_term = f"%{search}%"
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(getattr(self.model, field).ilike(search_term))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        return (await self.db.execute(query)).scalar() or 0

    async def create(self, obj_in: CreateSchemaType, exclude_fields: Optional[List[str]] = None) -> ModelType:
        """
        Membuat record baru dengan error handling standar
        exclude_fields: list of fields to exclude from creation (e.g., password confirmation)
        """
        try:
            exclude_set = set(exclude_fields) if exclude_fields is not None else None
            obj_data = obj_in.model_dump(exclude_unset=True, exclude=exclude_set)
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            db_obj_id = getattr(db_obj, "id", "unknown")
            logger.info(f"Successfully created {self.model_name} with ID: {db_obj_id}")
            return db_obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create {self.model_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal membuat {self.model_name}: {str(e)}"
            )

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update existing record dengan error handling standar"""
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await self.db.commit()
            await self.db.refresh(db_obj)
            db_obj_id = getattr(db_obj, "id", "unknown")
            logger.info(f"Successfully updated {self.model_name} with ID: {db_obj_id}")
            return db_obj
        except Exception as e:
            await self.db.rollback()
            db_obj_id = getattr(db_obj, "id", "unknown")
            logger.error(f"Failed to update {self.model_name} with ID {db_obj_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengupdate {self.model_name}: {str(e)}"
            )

    async def update_by_id(self, id: int, obj_in: UpdateSchemaType) -> ModelType:
        """Update record by ID dengan menggabungkan get_by_id dan update"""
        db_obj = await self.get_by_id(id)
        return await self.update(db_obj, obj_in)

    async def delete(self, id: int) -> None:
        """Delete record by ID dengan error handling standar"""
        db_obj = await self.get_by_id(id)
        try:
            await self.db.delete(db_obj)
            await self.db.commit()
            logger.info(f"Successfully deleted {self.model_name} with ID: {id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete {self.model_name} with ID {id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menghapus {self.model_name}: {str(e)}"
            )

    async def check_unique_constraint(self, field_name: str, value: Any, exclude_id: Optional[int] = None) -> bool:
        """
        Check apakah nilai pada field sudah ada (untuk validasi uniqueness)
        exclude_id: untuk exclude record tertentu (saat update)
        """
        query = select(self.model).where(getattr(self.model, field_name) == value)

        if exclude_id is not None:
            query = query.where(self.model.id != exclude_id)  # type: ignore

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        return existing is None

    async def validate_unique_fields(
        self, obj_data: Dict[str, Any], unique_fields: Optional[List[str]] = None, exclude_id: Optional[int] = None
    ) -> None:
        """
        Validate multiple unique fields dan raise HTTPException jika conflict
        """
        if unique_fields is not None:
            for field in unique_fields:
                if field in obj_data:
                    is_unique = await self.check_unique_constraint(
                        field_name=field, value=obj_data[field], exclude_id=exclude_id
                    )
                    if not is_unique:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT, detail=f"{field.title()} '{obj_data[field]}' sudah ada"
                        )


class PaginatedResponse(BaseModel, Generic[ModelType]):
    """Response model standar untuk paginated results"""

    data: Sequence[ModelType]
    total_count: int
    skip: int
    limit: Optional[int]

    @classmethod
    async def create(
        cls,
        service: BaseService,
        skip: int = 0,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by_field: str = "id",
        order_desc: bool = True,
    ) -> "PaginatedResponse[ModelType]":
        """Factory method untuk membuat paginated response"""
        data = await service.get_all(
            skip=skip,
            limit=limit,
            search=search,
            search_fields=search_fields,
            order_by_field=order_by_field,
            order_desc=order_desc,
        )
        total_count = await service.get_total_count(search=search, search_fields=search_fields)

        return cls(data=data, total_count=total_count, skip=skip, limit=limit)
