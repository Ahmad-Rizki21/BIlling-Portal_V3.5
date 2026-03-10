"""
Data Teknis Service Layer - Menghilangkan duplikasi business logic dari routers/data_teknis.py
Mengelola integrasi Mikrotik, validasi IP, dan data teknis pelanggan.
"""

import csv
import io
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import chardet
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..models.odp import ODP as ODPModel
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..schemas.data_teknis import DataTeknisCreate, DataTeknisUpdate, DataTeknisImport
from ..services import mikrotik_service
from ..websocket_manager import manager
from .base_service import BaseService

logger = logging.getLogger(__name__)

class DataTeknisService(BaseService[DataTeknisModel, DataTeknisCreate, DataTeknisUpdate]):
    """
    Service layer untuk manajemen Data Teknis.
    Menangani sinkronisasi ke Mikrotik dan notifikasi ke Finance.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(DataTeknisModel, db)

    async def create_data_teknis(self, data_teknis: DataTeknisCreate) -> DataTeknisModel:
        """
        Membuat data teknis baru, mengirim notifikasi ke Finance, 
        dan mendaftarkan secret di Mikrotik.
        """
        # 1. Validasi Pelanggan
        pelanggan = await self.db.get(
            PelangganModel,
            data_teknis.pelanggan_id,
            options=[selectinload(PelangganModel.harga_layanan)]
        )
        if not pelanggan:
            raise HTTPException(status_code=404, detail=f"Pelanggan dengan id {data_teknis.pelanggan_id} tidak ditemukan.")

        # 2. Cek Duplikasi
        existing = await self.db.execute(
            select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == data_teknis.pelanggan_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Data teknis untuk pelanggan ini sudah ada.")

        # 3. Validasi Server & ODP
        mikrotik_server = None
        if data_teknis.mikrotik_server_id:
            mikrotik_server = await self.db.get(MikrotikServerModel, data_teknis.mikrotik_server_id)
            if not mikrotik_server:
                raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan.")

        odp = None
        if data_teknis.odp_id:
            odp = await self.db.get(ODPModel, data_teknis.odp_id)
            if not odp:
                raise HTTPException(status_code=404, detail="ODP tidak ditemukan.")

        # 4. Simpan ke Database
        data_dict = data_teknis.model_dump(exclude={"pelanggan_id", "mikrotik_server_id", "odp_id", "odp"})
        db_obj = DataTeknisModel(**data_dict)
        db_obj.pelanggan_id = pelanggan.id
        if mikrotik_server:
            db_obj.mikrotik_server_id = mikrotik_server.id
            db_obj.olt = mikrotik_server.name # Konsistensi field 'olt'
        if odp:
            db_obj.odp_id = odp.id

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # 5. Kirim Notifikasi ke Finance
        await self._notify_finance(pelanggan.nama, pelanggan.id)

        # 6. Trigger Mikrotik Create
        try:
            await mikrotik_service.trigger_mikrotik_create(self.db, db_obj)
        except Exception as e:
            logger.error(f"Gagal membuat secret di Mikrotik untuk {db_obj.id_pelanggan}: {e}")

        # 7. Re-query untuk response serialization
        return await self.get_by_id_with_relations(
            db_obj.id, 
            relations=["pelanggan"]
        )

    async def update_data_teknis(self, data_teknis_id: int, data_teknis_update: DataTeknisUpdate) -> DataTeknisModel:
        """
        Update data teknis dan sinkronisasi perubahan ke Mikrotik.
        """
        db_obj = await self.db.get(
            DataTeknisModel,
            data_teknis_id,
            options=[
                joinedload(DataTeknisModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                joinedload(DataTeknisModel.pelanggan).joinedload(PelangganModel.langganan),
            ],
        )
        if not db_obj:
            raise HTTPException(status_code=404, detail="Data Teknis not found")

        old_id_pelanggan = db_obj.id_pelanggan
        
        # Update field-field yang dikirim
        update_data = data_teknis_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Trigger Mikrotik Update
        try:
            if db_obj.pelanggan and db_obj.pelanggan.langganan:
                langganan_terkait = db_obj.pelanggan.langganan[0]
                await mikrotik_service.trigger_mikrotik_update(self.db, langganan_terkait, db_obj, old_id_pelanggan)
        except Exception as e:
            logger.error(f"Gagal sinkronisasi update ke Mikrotik untuk {db_obj.id_pelanggan}: {e}")

        return db_obj

    async def check_ip_availability(self, ip_address: str, exclude_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Memeriksa ketersediaan IP address baik di DB maupun di seluruh Mikrotik.
        Returns: (is_taken, message, owner_id)
        """
        # 1. Cek di Database
        query = select(DataTeknisModel).where(DataTeknisModel.ip_pelanggan == ip_address)
        if exclude_id:
            query = query.where(DataTeknisModel.id != exclude_id)
        
        existing_in_db = (await self.db.execute(query)).scalar_one_or_none()
        if existing_in_db:
            return True, f"IP sudah terpakai di database oleh {existing_in_db.id_pelanggan}", existing_in_db.id_pelanggan

        # 2. Cek di Mikrotik
        all_servers = (await self.db.execute(select(MikrotikServerModel))).scalars().all()
        for server in all_servers:
            api, connection = mikrotik_service.get_api_connection(server)
            if api:
                try:
                    owner_name = mikrotik_service.check_ip_in_secrets(api, ip_address)
                    if owner_name:
                        return True, f"IP sudah terpakai di Mikrotik '{server.name}' oleh {owner_name}", owner_name
                finally:
                    if connection:
                        mikrotik_service.mikrotik_pool.return_connection(connection, server.host_ip, int(server.port))
        
        return False, "IP tersedia", None

    async def get_filtered_data_teknis_stmt(self, search: Optional[str] = None, olt: Optional[str] = None, 
                                            profile: Optional[str] = None, vlan: Optional[str] = None,
                                            onu_power_min: Optional[int] = None, onu_power_max: Optional[int] = None):
        """Membangun query statement untuk list data teknis dengan berbagai filter."""
        query = select(DataTeknisModel).options(
            joinedload(DataTeknisModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            joinedload(DataTeknisModel.mikrotik_server),
            joinedload(DataTeknisModel.odp)
        )

        if search:
            search_term = f"%{search}%"
            query = query.join(DataTeknisModel.pelanggan).where(
                or_(
                    PelangganModel.nama.ilike(search_term),
                    DataTeknisModel.id_pelanggan.ilike(search_term),
                    DataTeknisModel.ip_pelanggan.ilike(search_term),
                    DataTeknisModel.sn.ilike(search_term),
                )
            )

        if olt and olt != "Semua":
            query = query.where(DataTeknisModel.olt == olt)
        
        if profile and profile != "Semua":
            query = query.where(DataTeknisModel.profile_pppoe == profile)
            
        if vlan and vlan != "Semua":
            query = query.where(DataTeknisModel.id_vlan == vlan)

        if onu_power_min is not None:
            query = query.where(DataTeknisModel.onu_power >= onu_power_min)
        
        if onu_power_max is not None:
            query = query.where(DataTeknisModel.onu_power <= onu_power_max)

        return query

    async def _notify_finance(self, pelanggan_nama: str, pelanggan_id: int):
        """Kirim notifikasi ke user Finance via WebSocket."""
        try:
            finance_role_query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name) == "finance")
            result = await self.db.execute(finance_role_query)
            finance_user_ids = list(result.scalars().all())

            if finance_user_ids:
                notification_payload = {
                    "type": "new_technical_data",
                    "message": f"Data teknis untuk {pelanggan_nama} telah ditambahkan. Siap dibuatkan langganan.",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "pelanggan_id": pelanggan_id,
                        "pelanggan_nama": pelanggan_nama,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
                await manager.broadcast_to_roles(notification_payload, finance_user_ids)
        except Exception as e:
            logger.error(f"Gagal mengirim notifikasi ke Finance: {e}")

    async def import_from_csv(self, file: UploadFile) -> Dict[str, Any]:
        """Import data teknis dari CSV dengan validasi massal."""
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="File kosong.")

        try:
            encoding = chardet.detect(contents)["encoding"] or "utf-8"
            content_str = contents.decode(encoding)
            if content_str.startswith("\ufeff"):
                content_str = content_str.lstrip("\ufeff")

            first_line = content_str.split('\n')[0]
            delimiter = ";" if ";" in first_line and first_line.count(";") > first_line.count(",") else ","
            
            reader_object = csv.DictReader(io.StringIO(content_str), delimiter=delimiter)
            reader = list(reader_object)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Gagal memproses file CSV: {repr(e)}")

        # Optimisasi: Pre-fetch
        emails = {row.get("email_pelanggan", "").lower().strip() for row in reader if row.get("email_pelanggan")}
        servers_to_find = {row.get("olt", "").strip() for row in reader if row.get("olt")}
        odps_to_find = {row.get("kode_odp", "").strip() for row in reader if row.get("kode_odp")}

        pelanggan_q = await self.db.execute(select(PelangganModel).where(func.lower(PelangganModel.email).in_(emails)))
        pelanggan_map = {p.email.lower(): p for p in pelanggan_q.scalars().all()}

        server_q = await self.db.execute(select(MikrotikServerModel).where(MikrotikServerModel.name.in_(servers_to_find)))
        server_map = {s.name: s for s in server_q.scalars().all()}

        odp_q = await self.db.execute(select(ODPModel).where(ODPModel.kode_odp.in_(odps_to_find)))
        odp_map = {o.kode_odp: o for o in odp_q.scalars().all()}

        existing_teknis_q = await self.db.execute(
            select(DataTeknisModel.pelanggan_id).where(DataTeknisModel.pelanggan_id.in_([p.id for p in pelanggan_map.values()]))
        )
        existing_pelanggan_ids = set(existing_teknis_q.scalars().all())

        errors = []
        data_to_create = []
        processed_emails = set()

        for row_num, row in enumerate(reader, start=2):
            try:
                data_import = DataTeknisImport.model_validate(row)
                email = data_import.email_pelanggan.lower().strip()
                pelanggan = pelanggan_map.get(email)

                if not pelanggan:
                    errors.append(f"Baris {row_num}: Pelanggan email '{email}' tidak ditemukan.")
                    continue
                if email in processed_emails:
                    errors.append(f"Baris {row_num}: Email '{email}' duplikat di file.")
                    continue
                if pelanggan.id in existing_pelanggan_ids:
                    errors.append(f"Baris {row_num}: '{pelanggan.nama}' sudah punya data teknis.")
                    continue

                mikrotik_server = server_map.get(data_import.nama_mikrotik_server)
                if not mikrotik_server:
                    errors.append(f"Baris {row_num}: OLT '{data_import.nama_mikrotik_server}' tidak ada.")
                    continue

                odp_id = odp_map.get(data_import.kode_odp).id if data_import.kode_odp and data_import.kode_odp in odp_map else None

                teknis_data = data_import.model_dump(exclude={"email_pelanggan", "nama_mikrotik_server", "kode_odp"})
                teknis_data.update({
                    "pelanggan_id": pelanggan.id,
                    "mikrotik_server_id": mikrotik_server.id,
                    "odp_id": odp_id,
                    "olt": mikrotik_server.name
                })
                data_to_create.append(DataTeknisModel(**teknis_data))
                processed_emails.add(email)

            except Exception as e:
                errors.append(f"Baris {row_num}: {str(e)}")

        if errors:
            raise HTTPException(status_code=422, detail={"errors": errors})
        if not data_to_create:
            raise HTTPException(status_code=400, detail="Tidak ada data valid.")

        self.db.add_all(data_to_create)
        await self.db.commit()
        return {"message": f"Berhasil mengimpor {len(data_to_create)} data teknis baru."}

    async def get_available_profiles(self, paket_layanan_id: int, pelanggan_id: int, mikrotik_server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Mengambil daftar profile PPPoE yang relevan dari Mikrotik."""
        paket = await self.db.get(PaketLayananModel, paket_layanan_id)
        if not paket:
            raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan")

        # Tentukan server
        server_id = mikrotik_server_id
        if not server_id:
            data_teknis = (await self.db.execute(select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == pelanggan_id))).scalar_one_or_none()
            if data_teknis:
                server_id = data_teknis.mikrotik_server_id

        if not server_id:
            return []

        server = await self.db.get(MikrotikServerModel, server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan.")

        kecepatan_str = f"{paket.kecepatan}Mbps"
        api, connection = mikrotik_service.get_api_connection(server)
        if not api:
            raise HTTPException(status_code=503, detail="Tidak dapat terhubung ke Mikrotik.")

        try:
            all_profiles = mikrotik_service.get_all_ppp_profiles(api)
            relevant_profiles = [p for p in all_profiles if kecepatan_str in p]
            
            ppp_secrets = mikrotik_service.get_all_ppp_secrets(api)
            secret_profiles = [s.get("profile") for s in ppp_secrets if "profile" in s]
            from collections import Counter
            usage_map = Counter(secret_profiles)

            return [
                {"profile_name": p, "usage_count": usage_map.get(p, 0)}
                for p in sorted(relevant_profiles)
            ]
        finally:
            if connection:
                mikrotik_service.mikrotik_pool.return_connection(connection, server.host_ip, int(server.port))

    async def get_last_used_ip(self, mikrotik_server_id: int) -> Dict[str, Any]:
        """Menentukan IP terakhir yang digunakan di server tertentu (Mikrotik vs DB)."""
        server = await self.db.get(MikrotikServerModel, mikrotik_server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server tidak ditemukan.")

        api, connection = mikrotik_service.get_api_connection(server)
        last_ip = None
        source = "database"

        if api:
            try:
                secrets = mikrotik_service.get_all_ppp_secrets(api)
                ips = []
                for s in secrets:
                    ip = s.get("remote-address")
                    if ip and len(ip.split(".")) == 4:
                        ips.append(ip)
                
                if ips:
                    ips.sort(key=lambda x: int(x.split(".")[-1]), reverse=True)
                    last_ip = ips[0]
                    source = "mikrotik"
            except Exception as e:
                logger.error(f"Gagal akses Mikrotik: {e}")
            finally:
                if connection:
                    mikrotik_service.mikrotik_pool.return_connection(connection, server.host_ip, int(server.port))

        if not last_ip:
            q = select(DataTeknisModel).where(DataTeknisModel.mikrotik_server_id == mikrotik_server_id).order_by(DataTeknisModel.ip_pelanggan.desc()).limit(1)
            res = (await self.db.execute(q)).scalar_one_or_none()
            if res:
                last_ip = res.ip_pelanggan
        
        last_octet = int(last_ip.split(".")[-1]) if last_ip else 0
        return {
            "last_ip": last_ip,
            "last_octet": last_octet,
            "message": f"IP terakhir ({source}): {last_ip}" if last_ip else "Belum ada IP.",
            "server_name": server.name,
            "source": source
        }

    async def delete_data_teknis(self, data_teknis_id: int) -> None:
        """Menghapus data teknis dan secret di Mikrotik."""
        db_obj = await self.db.get(DataTeknisModel, data_teknis_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Data Teknis not found")

        id_pelanggan = db_obj.id_pelanggan
        server_id = db_obj.mikrotik_server_id

        if server_id:
            server = await self.db.get(MikrotikServerModel, server_id)
            if server:
                try:
                    api, connection = mikrotik_service.get_api_connection(server)
                    if api:
                        mikrotik_service.delete_pppoe_secret(api, id_pelanggan)
                except Exception as e:
                    logger.error(f"Gagal hapus secret Mikrotik {id_pelanggan}: {e}")
                finally:
                    if connection:
                        mikrotik_service.mikrotik_pool.return_connection(connection, server.host_ip, int(server.port))

        await self.db.delete(db_obj)
        await self.db.commit()

    async def get_distinct_values(self, field_name: str) -> List[str]:
        """Mengambil nilai unik dari kolom tertentu untuk filter dropdown."""
        if not hasattr(self.model, field_name):
            return []
        
        column = getattr(self.model, field_name)
        query = select(column).where(column.isnot(None)).distinct().order_by(column)
        result = await self.db.execute(query)
        values = result.scalars().all()
        return ["Semua"] + [str(v) for v in values if v]

# Factory function
def get_data_teknis_service(db: AsyncSession) -> DataTeknisService:
    return DataTeknisService(db)
