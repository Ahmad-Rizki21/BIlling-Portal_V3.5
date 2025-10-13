"""
Utility functions untuk validasi yang umum digunakan
Menghilangkan duplikasi validasi di seluruh aplikasi
"""

import chardet
import re
from typing import List, Optional, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """Kumpulan static methods untuk validasi file"""

    @staticmethod
    async def validate_csv_file(file: UploadFile) -> bytes:
        """
        Validasi file CSV dengan error handling standar
        Menghilangkan duplikasi validasi CSV di pelanggan.py dan data_teknis.py
        """
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File harus berformat .csv")

        contents: bytes = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File kosong.")

        return contents

    @staticmethod
    async def read_csv_contents(contents: bytes) -> str:
        """
        Membaca dan decode file CSV dengan encoding detection
        Menghilangkan duplikasi file reading logic
        """
        try:
            encoding = chardet.detect(contents)["encoding"] or "utf-8"
            content_str = contents.decode(encoding)
            return content_str
        except Exception as e:
            logger.error(f"Gagal membaca atau mem-parsing file CSV: {repr(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Gagal memproses file CSV: {repr(e)}")


class FieldValidator:
    """Kumpulan static methods untuk validasi field"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validasi format email dengan regex"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validasi format nomor telepon Indonesia"""
        # Basic validation untuk nomor telepon Indonesia
        pattern = r"^(\+62|62|0)[0-9]{9,13}$"
        return re.match(pattern, phone.replace(" ", "")) is not None

    @staticmethod
    def validate_nik(nik: str) -> bool:
        """Validasi format NIK (16 digit)"""
        return nik.isdigit() and len(nik) == 16

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validasi format IP address"""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip):
            return False

        # Check range 0-255 untuk setiap octet
        octets = ip.split(".")
        return all(0 <= int(octet) <= 255 for octet in octets)


class DatabaseValidator:
    """Kumpulan static methods untuk validasi database-related"""

    @staticmethod
    async def check_unique_field(
        db: AsyncSession, model_class: Any, field_name: str, value: str, exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check apakah nilai pada field sudah ada di database
        exclude_id: untuk exclude record tertentu (saat update)
        """
        query = select(model_class).where(getattr(model_class, field_name) == value)

        if exclude_id:
            query = query.where(model_class.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        return existing is None

    @staticmethod
    async def validate_email_uniqueness(
        db: AsyncSession, email: str, model_class: Any, exclude_id: Optional[int] = None
    ) -> None:
        """
        Validasi uniqueness email dan raise HTTPException jika conflict
        Menghilangkan duplikasi email validation di multiple routers
        """
        if not FieldValidator.validate_email(email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format email tidak valid")

        is_unique = await DatabaseValidator.check_unique_field(
            db=db, model_class=model_class, field_name="email", value=email, exclude_id=exclude_id
        )

        if not is_unique:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{email}' sudah ada")

    @staticmethod
    async def validate_multiple_unique_fields(
        db: AsyncSession, model_class: Any, data: dict, unique_fields: List[str], exclude_id: Optional[int] = None
    ) -> None:
        """
        Validasi multiple unique fields dalam satu panggilan
        Menghilangkan duplikasi validation logic
        """
        for field_name in unique_fields:
            if field_name in data:
                is_unique = await DatabaseValidator.check_unique_field(
                    db=db, model_class=model_class, field_name=field_name, value=data[field_name], exclude_id=exclude_id
                )

                if not is_unique:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT, detail=f"{field_name.title()} '{data[field_name]}' sudah ada"
                    )


class BusinessValidator:
    """Kumpulan static methods untuk validasi business logic"""

    @staticmethod
    def validate_installation_date(date_str: str) -> bool:
        """Validasi format tanggal instalasi"""
        try:
            from datetime import datetime

            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_paket_layanan_status(status: str) -> bool:
        """Validasi status paket layanan yang valid"""
        valid_statuses = ["Aktif", "Tidak Aktif", "Suspend", "Pending"]
        return status in valid_statuses

    @staticmethod
    def validate_invoice_status(status: str) -> bool:
        """Validasi status invoice yang valid"""
        valid_statuses = ["Draft", "Menunggu Pembayaran", "Lunas", "Jatuh Tempo", "Batal"]
        return status in valid_statuses

    @staticmethod
    def validate_mikrotik_connection_data(data: dict) -> bool:
        """Validasi data koneksi Mikrotik"""
        required_fields = ["host_ip", "port", "username", "password"]

        for field in required_fields:
            if field not in data or not data[field]:
                return False

        # Validasi IP address
        if not FieldValidator.validate_ip_address(data["host_ip"]):
            return False

        # Validasi port range
        try:
            port = int(data["port"])
            if not (1 <= port <= 65535):
                return False
        except ValueError:
            return False

        return True
