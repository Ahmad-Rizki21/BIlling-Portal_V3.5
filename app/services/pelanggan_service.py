"""
Pelanggan Service Layer - Menghilangkan duplikasi business logic dari routers
"""

from typing import List, Optional, Dict, Any, Tuple
import logging
import re
import io
import csv
import chardet
from datetime import datetime, date
from dateutil import parser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, text
from sqlalchemy.orm import joinedload, selectinload
from fastapi import HTTPException, status, UploadFile, Depends
from ..database import get_db

from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.role import Role as RoleModel
from ..models.user import User as UserModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.langganan import Langganan as LanggananModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..schemas.pelanggan import PelangganCreate, PelangganUpdate
from .base_service import BaseService
from ..websocket_manager import manager

logger = logging.getLogger(__name__)


class PelangganService(BaseService):
    """
    Service layer untuk Pelanggan dengan business logic terpusat.
    Mengonsolidasikan logika dari routers/pelanggan.py dan memisahkan tanggung jawab.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(PelangganModel, db)

    async def auto_update_langganan(self, pelanggan_id: int, old_layanan: str, new_layanan: str, id_brand: str) -> None:
        """
        Otomatis update langganan aktif pelanggan ketika layanan diubah.
        Logic ini diambil dan dioptimasi dari router.
        """
        try:
            # 1. Cari langganan aktif/suspended pelanggan
            langganan_query = (
                select(LanggananModel)
                .where(LanggananModel.pelanggan_id == pelanggan_id)
                .where(LanggananModel.status.in_(["Aktif", "Suspended"]))
                .options(joinedload(LanggananModel.paket_layanan))
            )
            langganan_result = await self.db.execute(langganan_query)
            active_langganans = langganan_result.scalars().all()
            active_langganan = active_langganans[0] if active_langganans else None

            if not active_langganan:
                logger.warning(f"Pelanggan {pelanggan_id} tidak memiliki langganan aktif atau suspended")
                return

            old_paket_name = active_langganan.paket_layanan.nama_paket if active_langganan.paket_layanan else "Unknown"

            # 2. Cari paket layanan yang sesuai dengan layanan baru
            paket_query = (
                select(PaketLayananModel)
                .where(PaketLayananModel.id_brand == id_brand)
                .where(PaketLayananModel.nama_paket.ilike(f"%{new_layanan}%"))
            )
            paket_result = await self.db.execute(paket_query)
            new_paket = paket_result.scalars().first()

            if not new_paket:
                # Coba extract speed dari layanan jika exact match gagal
                speed_match = re.search(r'(\d+)\s*Mbps', new_layanan, re.IGNORECASE)
                if speed_match:
                    speed = speed_match.group(1)
                    # Prioritas: Regex match "X Mbps"
                    paket_query_speed = (
                        select(PaketLayananModel)
                        .where(PaketLayananModel.id_brand == id_brand)
                        .where(PaketLayananModel.nama_paket.ilike(f"%{speed} Mbps%"))
                    )
                    paket_result_speed = await self.db.execute(paket_query_speed)
                    new_paket = paket_result_speed.scalars().first()
                    
                    if not new_paket:
                         paket_query_loose = (
                            select(PaketLayananModel)
                            .where(PaketLayananModel.id_brand == id_brand)
                            .where(PaketLayananModel.nama_paket.ilike(f"%{speed}%"))
                        )
                         paket_result_loose = await self.db.execute(paket_query_loose)
                         new_paket = paket_result_loose.scalars().first()

            if not new_paket:
                logger.error(f"Tidak menemukan paket untuk layanan '{new_layanan}' (brand: {id_brand})")
                return

            # 3. Update langganan ke paket baru
            active_langganan.paket_layanan_id = new_paket.id

            # Update harga dengan pajak dari brand
            brand_query = select(HargaLayananModel).where(HargaLayananModel.id_brand == id_brand)
            brand_result = await self.db.execute(brand_query)
            brand_info = brand_result.scalar_one_or_none()

            if brand_info:
                pajak_rate = float(brand_info.pajak) / 100
                new_harga = round(float(new_paket.harga) * (1 + pajak_rate), 0)
                active_langganan.harga_awal = new_harga

            self.db.add(active_langganan)
            logger.info(f"Update langganan: Pelanggan {pelanggan_id} {old_paket_name} -> {new_paket.nama_paket}")

        except Exception as e:
            logger.error(f"Gagal auto-update langganan pelanggan {pelanggan_id}: {e}", exc_info=True)

    async def create_pelanggan(self, pelanggan_data: Dict[str, Any]) -> PelangganModel:
        """Create pelanggan baru dan kirim notifikasi."""
        try:
            db_pelanggan = PelangganModel(**pelanggan_data)
            self.db.add(db_pelanggan)
            await self.db.flush()
            
            # Prepare notification
            target_roles = ["NOC", "CS", "Admin"]
            query = (
                select(UserModel.id)
                .join(RoleModel)
                .where(func.lower(RoleModel.name).in_([r.lower() for r in target_roles]))
            )
            result = await self.db.execute(query)
            target_user_ids = list(result.scalars().all())

            notification = None
            if target_user_ids:
                notification = {
                    "type": "new_customer_for_noc",
                    "message": f"Pelanggan baru '{db_pelanggan.nama}' telah ditambahkan. Segera buatkan Data Teknis.",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "pelanggan_id": db_pelanggan.id,
                        "pelanggan_nama": db_pelanggan.nama,
                        "alamat": db_pelanggan.alamat,
                        "no_telp": db_pelanggan.no_telp,
                    },
                }

            await self.db.commit()
            
            # Re-fetch the object with relations to ensure all fields (including timestamps) are loaded
            query = (
                select(PelangganModel)
                .where(PelangganModel.id == db_pelanggan.id)
                .options(joinedload(PelangganModel.harga_layanan), joinedload(PelangganModel.data_teknis))
            )
            result = await self.db.execute(query)
            db_pelanggan = result.unique().scalar_one()

            # Broadcast notification after successful commit
            if notification:
                try:
                    await manager.broadcast_to_roles(notification, target_user_ids)
                except Exception as ne:
                    logger.warning(f"Notification failed: {ne}")

            return db_pelanggan
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating pelanggan: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_pelanggan(self, pelanggan_id: int, update_data: Dict[str, Any]) -> PelangganModel:
        """Update pelanggan dan handle relasi serta auto-update langganan."""
        try:
            query = (
                select(PelangganModel)
                .where(PelangganModel.id == pelanggan_id)
                .options(joinedload(PelangganModel.harga_layanan), joinedload(PelangganModel.data_teknis))
            )
            result = await self.db.execute(query)
            db_pelanggan = result.scalar_one_or_none()

            if not db_pelanggan:
                raise HTTPException(status_code=404, detail="Pelanggan not found")

            # Extract fields that need special handling
            id_brand = update_data.pop("id_brand", None)
            mikrotik_server_id = update_data.pop("mikrotik_server_id", None)
            new_layanan = update_data.get("layanan")
            old_layanan = db_pelanggan.layanan

            # Handle id_brand relation
            if id_brand is not None:
                if id_brand:
                    brand_obj = await self.db.get(HargaLayananModel, id_brand)
                    if not brand_obj:
                        raise HTTPException(status_code=404, detail="Brand not found")
                    db_pelanggan.harga_layanan = brand_obj
                else:
                    db_pelanggan.harga_layanan = None # type: ignore

            # Handle mikrotik_server relation
            if mikrotik_server_id is not None:
                if mikrotik_server_id:
                    srv = await self.db.get(MikrotikServerModel, mikrotik_server_id)
                    if not srv:
                        raise HTTPException(status_code=404, detail="Server not found")
                    db_pelanggan.mikrotik_server = srv
                else:
                    db_pelanggan.mikrotik_server = None # type: ignore

            # Update other fields
            for key, value in update_data.items():
                setattr(db_pelanggan, key, value)

            # Auto-update langganan if service changed
            if new_layanan and new_layanan != old_layanan:
                await self.auto_update_langganan(pelanggan_id, old_layanan, new_layanan, db_pelanggan.id_brand)

            await self.db.commit()
            
            # Re-fetch with relations to ensure all fields (created_at, updated_at, etc) are loaded
            query = (
                select(PelangganModel)
                .where(PelangganModel.id == pelanggan_id)
                .options(joinedload(PelangganModel.harga_layanan), joinedload(PelangganModel.data_teknis))
            )
            result = await self.db.execute(query)
            db_pelanggan = result.unique().scalar_one()

            return db_pelanggan
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating pelanggan {pelanggan_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_pelanggan(self, filters: Dict[str, Any]) -> Tuple[List[PelangganModel], int]:
        """Fetch all pelanggan with complex filters and pagination."""
        skip = filters.get("skip", 0)
        limit = filters.get("limit", 15)
        search = filters.get("search")
        alamat = filters.get("alamat")
        id_brand = filters.get("id_brand")
        layanan = filters.get("layanan")
        tgl_from = filters.get("tgl_instalasi_from")
        tgl_to = filters.get("tgl_instalasi_to")
        connection_status = filters.get("connection_status")
        use_minimal = filters.get("use_minimal_loading", False)
        for_invoice = filters.get("for_invoice_selection", False)

        base_query = select(PelangganModel)
        count_query = select(func.count(PelangganModel.id))

        if search:
            st = f"%{search}%"
            cond = or_(
                PelangganModel.nama.ilike(st),
                PelangganModel.email.ilike(st),
                PelangganModel.no_telp.ilike(st)
            )
            base_query = base_query.where(cond)
            count_query = count_query.where(cond)

        if alamat:
            base_query = base_query.where(PelangganModel.alamat == alamat)
            count_query = count_query.where(PelangganModel.alamat == alamat)

        if id_brand:
            base_query = base_query.where(PelangganModel.id_brand == id_brand)
            count_query = count_query.where(PelangganModel.id_brand == id_brand)

        if layanan:
            base_query = base_query.where(PelangganModel.layanan == layanan)
            count_query = count_query.where(PelangganModel.layanan == layanan)

        if tgl_from:
            base_query = base_query.where(PelangganModel.tgl_instalasi >= tgl_from)
            count_query = count_query.where(PelangganModel.tgl_instalasi >= tgl_from)

        if tgl_to:
            base_query = base_query.where(PelangganModel.tgl_instalasi <= tgl_to)
            count_query = count_query.where(PelangganModel.tgl_instalasi <= tgl_to)

        if connection_status:
            if connection_status == "unconfigured":
                base_query = base_query.outerjoin(PelangganModel.data_teknis).where(DataTeknisModel.id == None)
                count_query = count_query.outerjoin(PelangganModel.data_teknis).where(DataTeknisModel.id == None)
            elif connection_status == "configured":
                base_query = base_query.join(PelangganModel.data_teknis)
                count_query = count_query.join(PelangganModel.data_teknis)

        total_count = (await self.db.execute(count_query)).scalar_one()

        if use_minimal or for_invoice:
            data_query = base_query.options(
                joinedload(PelangganModel.data_teknis),
                joinedload(PelangganModel.harga_layanan)
            )
        else:
            data_query = base_query.options(
                joinedload(PelangganModel.data_teknis),
                joinedload(PelangganModel.harga_layanan),
                selectinload(PelangganModel.langganan).joinedload(LanggananModel.paket_layanan)
            )

        data_query = data_query.order_by(PelangganModel.id.desc())
        if limit is not None:
            data_query = data_query.offset(skip).limit(limit)

        result = await self.db.execute(data_query)
        return list(result.scalars().unique().all()), total_count

    async def delete_pelanggan_cascade(self, pelanggan_id: int):
        """Perform cascade delete for a customer and all related data."""
        db_pelanggan = await self.db.get(PelangganModel, pelanggan_id)
        if not db_pelanggan:
            raise HTTPException(status_code=404, detail="Pelanggan not found")

        try:
            # Delete related data manually to ensure control
            await self.db.execute(text("DELETE FROM data_teknis WHERE pelanggan_id = :id"), {"id": pelanggan_id})
            await self.db.execute(text("DELETE FROM langganan WHERE pelanggan_id = :id"), {"id": pelanggan_id})
            await self.db.execute(text("DELETE FROM invoices WHERE pelanggan_id = :id"), {"id": pelanggan_id})
            
            await self.db.delete(db_pelanggan)
            await self.db.commit()
            logger.info(f"Cascade delete for customer {pelanggan_id} successful")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Cascade delete failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_unique_lokasi(self) -> List[str]:
        """Get unique customer addresses for filters."""
        query = select(PelangganModel.alamat).distinct().where(PelangganModel.alamat.isnot(None)).order_by(PelangganModel.alamat)
        result = await self.db.execute(query)
        return [loc for loc in result.scalars().all() if loc]

    async def bulk_import(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Bulk import customers from CSV with full validation and duplicate checking."""
        try:
            encoding = chardet.detect(file_content)["encoding"] or "utf-8"
            content_str = file_content.decode(encoding)
            if content_str.startswith("\ufeff"):
                content_str = content_str.lstrip("\ufeff")

            # Detect delimiter
            first_line = content_str.split('\n')[0]
            delim = ";" if ";" in first_line and first_line.count(";") > first_line.count(",") else ","

            reader = csv.DictReader(io.StringIO(content_str), delimiter=delim)
            if not reader.fieldnames:
                raise HTTPException(status_code=400, detail="Invalid CSV header")

            mapping = {
                "Nama": "nama", "No KTP": "no_ktp", "Email": "email",
                "No Telepon": "no_telp", "Alamat": "alamat", "Alamat 2": "alamat_2",
                "Blok": "blok", "Unit": "unit", "ID Brand": "id_brand",
                "Layanan": "layanan", "Tanggal Instalasi (YYYY-MM-DD)": "tgl_instalasi"
            }

            # Pre-load existing data for fast validation
            emails_q = await self.db.execute(select(func.lower(PelangganModel.email)))
            existing_emails = set(emails_q.scalars().all())
            ktp_q = await self.db.execute(select(PelangganModel.no_ktp))
            existing_ktp = set(ktp_q.scalars().all())

            new_customers = []
            errors = []
            file_emails = set()
            file_ktp = set()
            dummy_ktp = {"0000000000000000", "", "N/A", "NULL", "NONE"}

            for row_idx, row in enumerate(reader, start=2):
                data = {mapping.get(h, h): row.get(h, "").strip() for h in reader.fieldnames if mapping.get(h)}
                if not any(data.values()): continue

                try:
                    # Clean/Format data
                    email_clean = data.get("email", "").lower()
                    ktp_clean = data.get("no_ktp", "")
                    if ktp_clean in dummy_ktp: ktp_clean = "0000000000000000"

                    # Dupe checks
                    if email_clean in file_emails or email_clean in existing_emails:
                        errors.append(f"Row {row_idx}: Email '{email_clean}' duplikat")
                        continue
                    if ktp_clean != "0000000000000000" and (ktp_clean in file_ktp or ktp_clean in existing_ktp):
                        errors.append(f"Row {row_idx}: No KTP '{ktp_clean}' duplikat")
                        continue

                    # Date parsing
                    tgl_str = data.get("tgl_instalasi")
                    if tgl_str:
                        try:
                            data["tgl_instalasi"] = parser.parse(tgl_str).date()
                        except:
                            errors.append(f"Row {row_idx}: Tanggal tidak valid")
                            continue
                    else:
                        data["tgl_instalasi"] = None

                    new_customers.append(PelangganModel(**data))
                    file_emails.add(email_clean)
                    if ktp_clean != "0000000000000000": file_ktp.add(ktp_clean)

                except Exception as row_error:
                    errors.append(f"Row {row_idx}: {str(row_error)}")

            if errors:
                return {"success": False, "error_count": len(errors), "errors": errors[:50]}

            if new_customers:
                self.db.add_all(new_customers)
                await self.db.commit()
                return {"success": True, "count": len(new_customers), "message": f"Berhasil mengimpor {len(new_customers)} pelanggan"}
            
            return {"success": True, "count": 0, "message": "Tidak ada data yang diimpor"}

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


def get_pelanggan_service(db: AsyncSession = Depends(get_db)) -> PelangganService:
    """Factory function for PelangganService dependency injection."""
    return PelangganService(db)
