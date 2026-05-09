import httpx
import logging
from ..config import settings
from typing import Optional

logger = logging.getLogger("app.services.whatsapp")

async def send_whatsapp_message(to_number: str, message: str) -> bool:
    """
    Kirim pesan WhatsApp menggunakan Watzap API (Watzap.id)
    """
    if not settings.WATZAP_API_KEY or not settings.WATZAP_NUMBER_KEY:
        logger.warning("WATZAP_API_KEY atau WATZAP_NUMBER_KEY belum dikonfigurasi di .env")
        return False

    url = "https://api.watzap.id/v1/send_message"
    
    payload = {
        "api_key": settings.WATZAP_API_KEY,
        "number_key": settings.WATZAP_NUMBER_KEY,
        "phone_no": to_number,
        "message": message
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success":
                logger.info(f"✅ Pesan WA berhasil dikirim ke {to_number}")
                return True
            else:
                logger.error(f"❌ Gagal kirim WA ke {to_number}: {result.get('message')}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Exception saat kirim WA ke {to_number}: {str(e)}")
        return False

async def get_technician_phone(db, technician_id: int) -> Optional[str]:
    """
    Ambil nomor telepon teknisi dari tabel system_settings.
    Format key di system_settings: 'TECHNICIAN_PHONE_ID_{technician_id}'
    """
    from ..models.system_setting import SystemSetting
    from sqlalchemy.future import select

    stmt = select(SystemSetting.setting_value).where(
        SystemSetting.setting_key == f"TECHNICIAN_PHONE_ID_{technician_id}"
    )
    result = await db.execute(stmt)
    phone = result.scalar_one_or_none()
    
    return phone
