"""
WhatsApp Opt-in Management
Endpoint untuk mengelola customer opt-in ke WhatsApp notifications
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.pelanggan import Pelanggan as PelangganModel
from ..database import get_db
import httpx
import base64
import logging
from ..config import settings

logger = logging.getLogger("app.routers.whatsapp_optin")

router = APIRouter(
    prefix="/whatsapp-optin",
    tags=["WhatsApp Opt-in"],
    responses={404: {"description": "Not found"}},
)


@router.post("/opt-in/{pelanggan_id}")
async def opt_in_customer(pelanggan_id: int, db: AsyncSession = Depends(get_db)):
    """
    Request opt-in for WhatsApp notifications untuk customer tertentu.

    Args:
        pelanggan_id: ID pelanggan yang mau di-opt-in

    Returns:
    - success: Status opt-in request
    - message: Description hasil
    - xendit_response: Response dari Xendit API
    """

    # Cari pelanggan
    stmt = select(PelangganModel).where(PelangganModel.id == pelanggan_id)
    result = await db.execute(stmt)
    pelanggan = result.scalar_one_or_none()

    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    if not pelanggan.no_telp:
        raise HTTPException(status_code=400, detail="Pelanggan tidak memiliki nomor telepon")

    # Format nomor telepon untuk WhatsApp
    clean_phone = "".join(filter(str.isdigit, pelanggan.no_telp))
    if clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]
    elif not clean_phone.startswith("62"):
        clean_phone = "62" + clean_phone
    whatsapp_number = "+" + clean_phone

    # Prepare Xendit API request - gunakan API key yang sama dengan invoice
    target_key_name = pelanggan.harga_layanan.xendit_key_name if pelanggan.harga_layanan else None
    if not target_key_name:
        target_key_name = "ajn-01"  # Fallback ke default key

    api_key = settings.XENDIT_API_KEYS.get(target_key_name)
    if not api_key:
        raise HTTPException(status_code=500, detail=f"Xendit API key for '{target_key_name}' not found")

    encoded_key = base64.b64encode(f"{api_key}:".encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "phone_number": whatsapp_number,
        "opt_in_type": "transactional"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.xendit.co/whatsapp/opt-ins",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ WhatsApp opt-in requested for {pelanggan.nama} ({whatsapp_number})")
            logger.info(f"Xendit response: {result}")

            return {
                "success": True,
                "message": f"Opt-in WhatsApp berhasil diajukan untuk {pelanggan.nama}",
                "pelanggan": {
                    "id": pelanggan.id,
                    "nama": pelanggan.nama,
                    "no_telp": whatsapp_number
                },
                "xendit_response": result
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ WhatsApp opt-in failed: {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Gagal request WhatsApp opt-in: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"❌ WhatsApp opt-in error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error saat request WhatsApp opt-in: {str(e)}"
        )


@router.get("/status/{pelanggan_id}")
async def check_optin_status(pelanggan_id: int, db: AsyncSession = Depends(get_db)):
    """
    Check opt-in status untuk customer tertentu.

    Args:
        pelanggan_id: ID pelanggan

    Returns:
    - success: Status check
    - pelanggan: Data pelanggan
    - whatsapp_number: Nomor WhatsApp yang terdaftar
    - opt_in_status: Status opt-in (jika ada data)
    """

    stmt = select(PelangganModel).where(PelangganModel.id == pelanggan_id)
    result = await db.execute(stmt)
    pelanggan = result.scalar_one_or_none()

    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    # Format nomor telepon
    clean_phone = "".join(filter(str.isdigit, pelanggan.no_telp))
    if clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]
    elif not clean_phone.startswith("62"):
        clean_phone = "62" + clean_phone
    whatsapp_number = "+" + clean_phone

    return {
        "success": True,
        "pelanggan": {
            "id": pelanggan.id,
            "nama": pelanggan.nama,
            "email": pelanggan.email,
            "no_telp": pelanggan.no_telp,
            "whatsapp_number": whatsapp_number
        },
        "status": "Ready for opt-in request",
        "note": "Gunakan POST /opt-in/{pelanggan_id} untuk request opt-in"
    }


@router.post("/test-message/{pelanggan_id}")
async def test_whatsapp_message(pelanggan_id: int, message: str, db: AsyncSession = Depends(get_db)):
    """
    Kirim test WhatsApp message (jika sudah di-opt-in).
    Hanya untuk testing purposes.

    Args:
        pelanggan_id: ID pelanggan
        message: Pesan test yang ingin dikirim

    Returns:
    - success: Status pengiriman
    - message: Hasil test
    """

    stmt = select(PelangganModel).where(PelangganModel.id == pelanggan_id)
    result = await db.execute(stmt)
    pelanggan = result.scalar_one_or_none()

    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    # Format nomor telepon
    clean_phone = "".join(filter(str.isdigit, pelanggan.no_telp))
    if clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]
    elif not clean_phone.startswith("62"):
        clean_phone = "62" + clean_phone
    whatsapp_number = "+" + clean_phone

    return {
        "success": True,
        "message": f"Test message untuk {pelanggan.nama} ({whatsapp_number})",
        "test_message": message,
        "note": "Silakan cek WhatsApp customer apakah pesan diterima",
        "next_steps": [
            "1. Jika pesan diterima: Opt-in berhasil",
            "2. Jika pesan tidak diterima: Perlu opt-in manual",
            "3. Hubungi customer untuk opt-in via WhatsApp"
        ]
    }