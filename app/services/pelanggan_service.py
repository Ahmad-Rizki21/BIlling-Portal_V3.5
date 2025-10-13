"""
Pelanggan Service Layer - Menghilangkan duplikasi business logic dari routers
"""

from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.role import Role as RoleModel
from ..models.user import User as UserModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..schemas.pelanggan import PelangganCreate, PelangganUpdate
from ..services.base_service import BaseService, PaginatedResponse
from ..utils.validators import DatabaseValidator, FieldValidator  # type: ignore
from ..utils.error_handler import ErrorHandler, SuccessHandler, handle_errors  # type: ignore
from ..utils.csv_export import CSVExporter, ExportConfigurations  # type: ignore
from ..services.notification_service import NotificationService
from ..constants import Status, Pagination, Validation, HTTPMessages  # type: ignore

logger = logging.getLogger(__name__)


class PelangganService(BaseService[PelangganModel, PelangganCreate, PelangganUpdate]):
    """
    Service layer untuk Pelanggan dengan business logic terpusat
    Menghilangkan duplikasi logic dari routers/pelanggan.py
    """

    def __init__(self, db: AsyncSession):
        super().__init__(PelangganModel, db)
        self.search_fields = ["nama", "email", "no_telp"]

    @handle_errors("membuat pelanggan baru")
    async def create_pelanggan(self, pelanggan_data: PelangganCreate, current_user_id: int) -> PelangganModel:
        """
        Create pelanggan baru dengan validasi lengkap dan notification
        Menghilangkan duplikasi create logic dari router
        """
        # Validate required fields
        await self._validate_create_data(pelanggan_data)

        # Check unique constraints
        await DatabaseValidator.validate_multiple_unique_fields(
            self.db, PelangganModel, pelanggan_data.model_dump(), ["email", "no_ktp"]
        )

        # Create pelanggan
        pelanggan_obj = await self.create(pelanggan_data)

        # Send notification to relevant teams
        await self._notify_new_pelanggan(pelanggan_obj)

        # Log success
        SuccessHandler.log_success(
            operation="membuat",
            resource_name="pelanggan",
            identifier=pelanggan_obj.id,
            additional_info={"created_by": current_user_id},
        )

        return pelanggan_obj

    @handle_errors("mengupdate pelanggan")
    async def update_pelanggan(
        self, pelanggan_id: int, pelanggan_data: PelangganUpdate, current_user_id: int
    ) -> PelangganModel:
        """
        Update pelanggan dengan validasi dan error handling
        """
        # Get existing pelanggan
        pelanggan = await self.get_by_id(pelanggan_id)

        # Validate update data
        await self._validate_update_data(pelanggan_data, pelanggan_id)

        # Check unique constraints (exclude current record)
        update_dict = pelanggan_data.model_dump(exclude_unset=True)
        if update_dict:
            await DatabaseValidator.validate_multiple_unique_fields(
                self.db, PelangganModel, update_dict, ["email", "no_ktp"], exclude_id=pelanggan_id
            )

        # Update pelanggan
        updated_pelanggan = await self.update(pelanggan, pelanggan_data)

        # Log success
        SuccessHandler.log_success(
            operation="mengupdate",
            resource_name="pelanggan",
            identifier=pelanggan_id,
            additional_info={"updated_by": current_user_id},
        )

        return updated_pelanggan

    async def get_pelanggan_with_relations(self, pelanggan_id: int) -> PelangganModel:
        """
        Get pelanggan dengan relasi (harga_layanan, data_teknis)
        Menghilangkan duplikasi query logic
        """
        return await self.get_by_id_with_relations(pelanggan_id, relations=["harga_layanan", "data_teknis"])

    async def search_pelanggan(
        self,
        skip: int = 0,
        limit: Optional[int] = Pagination.DEFAULT_PAGE_SIZE,
        search: Optional[str] = None,
        alamat: Optional[str] = None,
        id_brand: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search pelanggan dengan multiple filters dan field selection
        Menghilangkan duplikasi search logic
        """
        try:
            # Base query
            query = select(PelangganModel)

            # Apply search filter
            if search and len(search) >= Pagination.MIN_SEARCH_LENGTH:
                search_term = f"%{search}%"
                search_conditions = [
                    PelangganModel.nama.ilike(search_term),
                    PelangganModel.email.ilike(search_term),
                    PelangganModel.no_telp.ilike(search_term),
                ]
                query = query.where(or_(*search_conditions))

            # Apply other filters
            if alamat:
                query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))

            if id_brand:
                query = query.where(PelangganModel.id_brand == id_brand)

            # Get total count
            count_query = select(func.count(PelangganModel.id))
            if search and len(search) >= Pagination.MIN_SEARCH_LENGTH:
                search_term = f"%{search}%"
                search_conditions = [
                    PelangganModel.nama.ilike(search_term),
                    PelangganModel.email.ilike(search_term),
                    PelangganModel.no_telp.ilike(search_term),
                ]
                count_query = count_query.where(or_(*search_conditions))

            if alamat:
                count_query = count_query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))

            if id_brand:
                count_query = count_query.where(PelangganModel.id_brand == id_brand)

            total_count = (await self.db.execute(count_query)).scalar() or 0

            # Apply pagination and ordering
            query = query.order_by(PelangganModel.id.desc())

            if limit is not None:
                query = query.offset(skip).limit(limit)

            # Execute query with eager loading
            query = query.options(
                joinedload(PelangganModel.harga_layanan),
                joinedload(PelangganModel.data_teknis),
            )

            pelanggan_list = (await self.db.execute(query)).scalars().all()

            # Apply field selection if specified
            if fields:
                field_list = [f.strip() for f in fields.split(",")]
                pelanggan_list = [self._select_fields(pelanggan, field_list) for pelanggan in pelanggan_list]

            return {"data": pelanggan_list, "total_count": total_count, "skip": skip, "limit": limit}

        except Exception as e:
            ErrorHandler.handle_internal_server_error(
                e, "search pelanggan", {"skip": skip, "limit": limit, "search": search, "alamat": alamat, "id_brand": id_brand}
            )
            return {"data": [], "total_count": 0, "skip": skip, "limit": limit}

    async def export_to_csv(
        self,
        skip: int = 0,
        limit: int = Pagination.DEFAULT_EXPORT_LIMIT,
        search: Optional[str] = None,
        alamat: Optional[str] = None,
        id_brand: Optional[str] = None,
    ):
        """
        Export pelanggan data ke CSV dengan format standar
        Menghilangkan duplikasi export logic
        """
        try:
            # Get data dengan filter yang sama seperti search
            search_result = await self.search_pelanggan(
                skip=skip, limit=min(limit, Pagination.MAX_EXPORT_LIMIT), search=search, alamat=alamat, id_brand=id_brand
            )

            # Prepare data untuk export
            config = ExportConfigurations.PELANGGAN_EXPORT
            processed_data = CSVExporter.prepare_export_data(
                search_result["data"],
                field_mapping=config["field_mapping"],
                exclude_fields=config["exclude_fields"],
                transform_functions=config["transform_functions"],
            )

            # Create CSV response
            return CSVExporter.create_csv_response(processed_data, "pelanggan", config["headers"])

        except Exception as e:
            ErrorHandler.handle_internal_server_error(
                e,
                "export pelanggan CSV",
                {"limit": limit, "filters": {"search": search, "alamat": alamat, "id_brand": id_brand}},
            )

    async def import_from_csv(self, csv_data: List[Dict[str, Any]], current_user_id: int) -> Dict[str, Any]:
        """
        Import pelanggan dari CSV data dengan validasi
        Menghilangkan duplikasi import logic
        """
        try:
            created_count = 0
            error_count = 0
            errors = []

            for row_num, row_data in enumerate(csv_data, start=1):
                try:
                    # Validate and map data
                    pelanggan_data = self._map_csv_to_model(row_data)

                    # Validate data
                    await self._validate_create_data(pelanggan_data)

                    # Check uniqueness
                    await DatabaseValidator.validate_multiple_unique_fields(
                        self.db, PelangganModel, pelanggan_data.model_dump(), ["email", "no_ktp"]
                    )

                    # Create pelanggan
                    await self.create(pelanggan_data)
                    created_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({"row": row_num, "data": row_data.get("Nama", "Unknown"), "error": str(e)})

            # Send notification for batch import
            if created_count > 0:
                await NotificationService.send_system_notification(
                    self.db,
                    f"Import batch selesai: {created_count} pelanggan baru berhasil diimport",
                    "batch_import_complete",
                    data={"created_count": created_count, "error_count": error_count, "imported_by": current_user_id},
                )

            return {
                "message": f"Import selesai. {created_count} pelanggan berhasil dibuat, {error_count} gagal.",
                "created_count": created_count,
                "error_count": error_count,
                "errors": errors[:10],  # Return only first 10 errors
            }

        except Exception as e:
            ErrorHandler.handle_internal_server_error(
                e, "import pelanggan CSV", {"row_count": len(csv_data), "imported_by": current_user_id}
            )
            return {
                "message": "Import failed due to an error",
                "created_count": 0,
                "error_count": len(csv_data),
                "errors": [{"error": str(e)}],
            }

    async def get_unique_lokasi(self) -> List[str]:
        """
        Get unique locations untuk filter dropdown
        Menghilangkan duplikasi query logic
        """
        try:
            query = (
                select(PelangganModel.alamat)
                .where(PelangganModel.alamat.isnot(None))
                .distinct()
                .order_by(PelangganModel.alamat)
            )
            result = await self.db.execute(query)
            lokasi_list = result.scalars().all()
            return [lokasi for lokasi in lokasi_list if lokasi and lokasi.strip()]

        except Exception as e:
            ErrorHandler.handle_internal_server_error(e, "get unique lokasi")
            return []

    # Private helper methods

    async def _validate_create_data(self, pelanggan_data: PelangganCreate) -> None:
        """Validate data untuk create pelanggan"""
        # Validate email format
        if not FieldValidator.validate_email(pelanggan_data.email):
            raise ErrorHandler.handle_bad_request("Format email tidak valid")

        # Validate phone format
        if not FieldValidator.validate_phone_number(pelanggan_data.no_telp):
            raise ErrorHandler.handle_bad_request("Format nomor telepon tidak valid")

        # Validate NIK format
        if not FieldValidator.validate_nik(pelanggan_data.no_ktp):
            raise ErrorHandler.handle_bad_request("NIK harus 16 digit angka")

    async def _validate_update_data(self, pelanggan_data: PelangganUpdate, exclude_id: int) -> None:
        """Validate data untuk update pelanggan"""
        update_dict = pelanggan_data.model_dump(exclude_unset=True)

        # Validate email if provided
        if "email" in update_dict:
            if not FieldValidator.validate_email(update_dict["email"]):
                raise ErrorHandler.handle_bad_request("Format email tidak valid")

        # Validate phone if provided
        if "no_telp" in update_dict:
            if not FieldValidator.validate_phone_number(update_dict["no_telp"]):
                raise ErrorHandler.handle_bad_request("Format nomor telepon tidak valid")

        # Validate NIK if provided
        if "no_ktp" in update_dict:
            if not FieldValidator.validate_nik(update_dict["no_ktp"]):
                raise ErrorHandler.handle_bad_request("NIK harus 16 digit angka")

    def _select_fields(self, pelanggan: PelangganModel, fields: List[str]) -> Dict[str, Any]:
        """Select specific fields dari pelanggan object"""
        result = {"id": pelanggan.id}  # Always include ID  # type: ignore

        for field in fields:
            if hasattr(pelanggan, field):
                value = getattr(pelanggan, field)
                if hasattr(value, "__dict__"):  # Handle related objects
                    value = str(value)
                result[field] = value  # type: ignore

        return result

    def _map_csv_to_model(self, row_data: Dict[str, Any]) -> PelangganCreate:
        """Map CSV row data ke PelangganCreate schema"""
        # Map CSV columns ke model fields
        field_mapping = {
            "Nama": "nama",
            "No KTP": "no_ktp",
            "Email": "email",
            "No Telepon": "no_telp",
            "Layanan": "layanan",
            "Alamat": "alamat",
            "Alamat 2": "alamat_2",
            "Blok": "blok",
            "Unit": "unit",
            "Tanggal Instalasi (YYYY-MM-DD)": "tanggal_instalasi",
            "ID Brand": "id_brand",
        }

        mapped_data = {}
        for csv_field, model_field in field_mapping.items():
            if csv_field in row_data:
                mapped_data[model_field] = row_data[csv_field].strip()

        return PelangganCreate(**mapped_data)

    async def _notify_new_pelanggan(self, pelanggan: PelangganModel) -> None:
        """Send notification untuk pelanggan baru"""
        try:
            customer_data = {
                "id": pelanggan.id,
                "nama": pelanggan.nama,
                "alamat": pelanggan.alamat,
                "no_telp": pelanggan.no_telp,
                "email": pelanggan.email,
            }

            await NotificationService.notify_new_customer(self.db, customer_data)

        except Exception as e:
            # Log error tapi tidak gagalkan operasi
            logger.error(f"Failed to send notification for new pelanggan {pelanggan.id}: {e}")


# Factory function untuk dependency injection
def get_pelanggan_service(db: AsyncSession) -> PelangganService:
    """Factory function untuk PelangganService dependency injection"""
    return PelangganService(db)
