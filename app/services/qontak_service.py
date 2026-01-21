import hmac
import hashlib
import base64
import httpx
import logging
import locale
from datetime import datetime, timezone
from typing import Dict, Any

from ..config import settings

logger = logging.getLogger("app.services.qontak")


def generate_hmac_signature(
    client_id: str,
    client_secret: str,
    date: str,
    method: str,
    path: str
) -> str:
    """
    Generate HMAC signature for Qontak API authentication.

    Format: date: {date}\\n{method} {path} HTTP/1.1
    """
    string_to_sign = f"date: {date}\n{method} {path} HTTP/1.1"
    signature = hmac.new(
        client_secret.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()


def build_auth_headers(
    client_id: str,
    client_secret: str,
    method: str,
    path: str
) -> Dict[str, str]:
    """Build authorization headers dengan HMAC signature."""
    # Set locale ke 'C' untuk date format dalam bahasa Inggris
    original_locale = locale.getlocale()
    try:
        locale.setlocale(locale.LC_TIME, 'C')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        except locale.Error:
            pass

    date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Restore locale
    try:
        locale.setlocale(locale.LC_TIME, original_locale[0] or 'C')
    except locale.Error:
        pass

    string_to_sign = f"date: {date}\n{method} {path} HTTP/1.1"
    signature = generate_hmac_signature(client_id, client_secret, date, method, path)

    auth_header = (
        f'hmac username="{client_id}", '
        f'algorithm="hmac-sha256", '
        f'headers="date request-line", '
        f'signature="{signature}"'
    )

    logger.info(f"=== QONTAK API REQUEST ===")
    logger.info(f"Method: {method}")
    logger.info(f"Path: {path}")
    logger.info(f"Date: {date}")
    logger.info(f"String to Sign: {repr(string_to_sign)}")
    logger.info(f"Signature: {signature}")
    logger.info(f"==========================")

    return {
        "Authorization": auth_header,
        "Date": date,
        "Content-Type": "application/json",
    }


async def send_whatsapp_broadcast(
    langganan,
    phone_number: str
) -> Dict[str, Any]:
    """
    Send WhatsApp broadcast via Qontak API.

    Menggunakan endpoint direct broadcast:
    POST /v1/broadcasts/whatsapp/direct
    """
    # Get brand_id
    brand_id = langganan.pelanggan.harga_layanan.id_brand

    # Get channel_id and template_id based on brand
    channel_id = settings.QONTAK_CHANNEL_IDS.get(brand_id)
    template_id = settings.QONTAK_TEMPLATE_IDS.get(brand_id)

    if not channel_id:
        raise ValueError(f"No channel_id configured for brand: {brand_id}")
    if not template_id:
        raise ValueError(f"No template_id configured for brand: {brand_id}")

    # Build request payload sesuai dokumentasi
    # Template TIDAK PUNYA variable (0 variable), jadi parameters kosong
    customer_name = langganan.pelanggan.nama or "Pelanggan"
    
    payload = {
        "to_name": customer_name,
        "to_number": phone_number,
        "message_template_id": template_id,
        "channel_integration_id": channel_id,
        "language": {"code": "id"},
        "parameters": {}  # Kosong karena template tidak punya variable
    }

    # Path dan URL yang benar
    # Base URL: https://api.mekari.com/qontak/chat/v1
    # Endpoint: /broadcasts/whatsapp/direct (POST)
    path = "/qontak/chat/v1/broadcasts/whatsapp/direct"
    url = f"https://api.mekari.com{path}"

    headers = build_auth_headers(
        settings.QONTAK_CLIENT_ID,
        settings.QONTAK_CLIENT_SECRET,
        "POST",
        path
    )

    logger.info(f"Sending WhatsApp to {phone_number} (brand: {brand_id})")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        response.raise_for_status()
        result = response.json()
        return result
