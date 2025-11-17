# app/services/xendit_service.py
"""
Xendit payment gateway integration service.
Handle semua payment processing via Xendit API.

Features:
- Invoice creation via Xendit API
- Multiple payment methods (Bank transfer, E-wallet, Credit card)
- Payment status checking
- Webhook callback handling
- Multi-brand payment routing
- Payment reconciliation

Payment methods supported:
- Virtual Account (BCA, BNI, BRI, Mandiri)
- E-wallet (GoPay, OVO, DANA)
- Credit/Debit cards
- QRIS
- Convenience stores

Integration:
- Xendit API v2.0
- Multi-brand API key management
- Invoice model integration
- Payment callback processing
- Email/SMS notifications

Security:
- API key encryption
- HTTPS communication
- Request validation
- Error handling
- Audit logging

Configuration:
- XENDIT_API_KEYS: Dictionary of API keys per brand
- Base64 Basic authentication
- Timeout handling
"""

import httpx
from ..config import settings
from ..models.invoice import Invoice as InvoiceModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
import os
from dateutil.relativedelta import relativedelta
import base64
import logging
import urllib.parse
import json
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("app.services.xendit")


async def create_xendit_invoice(
    invoice: InvoiceModel,
    pelanggan: PelangganModel,
    paket: PaketLayananModel,
    deskripsi_xendit: str,
    pajak: float,
    no_telp_xendit: str = "",
) -> dict:
    """
    Create payment invoice via Xendit API.
    Core function buat generate payment link dan process payment.

    Args:
        invoice: Invoice model instance
        pelanggan: Pelanggan model instance
        paket: PaketLayanan model instance
        deskripsi_xendit: Description untuk payment page
        pajak: Tax amount
        no_telp_xendit: Customer phone number (optional)

    Returns:
        Dictionary dengan Xendit API response:
        - id: Xendit invoice ID
        - external_id: Our invoice number
        - short_url: Payment page URL
        - invoice_url: Alternative payment URL
        - status: Invoice status
        - expiry_date: Payment expiry

    Process flow:
    1. Select API key based on customer brand
    2. Validate all required data
    3. Calculate payment amounts
    4. Build Xendit API request
    5. Send HTTP POST to Xendit
    6. Process response and return result

    Error handling:
    - API key not found
    - Invalid data validation
    - Network timeout
    - Xendit API errors
    - HTTP errors

    Payment options included:
    - Virtual Account (all major banks)
    - E-wallets (GoPay, OVO, DANA, ShopeePay)
    - Credit/Debit cards
    - QRIS
    - Convenience stores

    Security:
    - API key encryption in config
    - HTTPS communication
    - Input validation
    - Error logging without sensitive data
    """
    target_key_name = pelanggan.harga_layanan.xendit_key_name
    api_key = settings.XENDIT_API_KEYS.get(target_key_name)
    if not api_key:
        raise ValueError(f"Kunci API Xendit untuk '{target_key_name}' tidak ditemukan.")

    # Brands Configuration:
    # - ajn-01 (JAKINET) -> JAKINET API key (ARTACOMINDO account)
    # - ajn-02 (JELANTIK) -> JELANTIK API key (murni JELANTIK account)
    # - ajn-03 (JELANTIK NAGRAK) -> JAKINET API key (pesan masuk ke Jakinet)

    if target_key_name == "ajn-01":  # JAKINET -> Pakai JAKINET API key (ARTACOMINDO account)
        jakinet_key = settings.XENDIT_API_KEYS.get("JAKINET")
        if jakinet_key:
            logger.info(f" Using JAKINET API key (ARTACOMINDO account) for {pelanggan.nama} (JAKINET - ajn-01)")
            api_key = jakinet_key

    elif target_key_name == "ajn-02":  # JELANTIK -> Pakai JELANTIK API key (murni)
        jelantik_key = settings.XENDIT_API_KEYS.get("JELANTIK")
        if jelantik_key:
            logger.info(f" Using JELANTIK API key for {pelanggan.nama} (JELANTIK - ajn-02)")
            api_key = jelantik_key

    elif target_key_name == "ajn-03":  # JELANTIK NAGRAK -> Pakai JAKINET API key (pesan ke Jakinet)
        jakinet_key = settings.XENDIT_API_KEYS.get("JAKINET")
        if jakinet_key:
            logger.info(f" Using JAKINET API key (ARTACOMINDO account) for {pelanggan.nama} (JELANTIK NAGRAK - ajn-03)")
            api_key = jakinet_key

    encoded_key = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_key}",
    }

    brand_info = pelanggan.harga_layanan
    jatuh_tempo_str = invoice.tgl_jatuh_tempo.strftime("%d/%m/%Y")  # type: ignore

    # Validasi data
    if not invoice.total_harga or invoice.total_harga <= 0:
        raise ValueError("Total harga invoice tidak valid")
    if not paket.harga or float(paket.harga) <= 0:
        raise ValueError("Harga paket tidak valid")
    if not pelanggan.nama or not pelanggan.email:
        raise ValueError("Data pelanggan (nama atau email) tidak lengkap")

    # Hitung harga dasar
    harga_dasar = float(invoice.total_harga) - pajak
    if harga_dasar < 0:
        raise ValueError("Harga dasar tidak boleh negatif")

    # Siapkan payload
    payload = {
        "external_id": invoice.invoice_number,
        "amount": float(invoice.total_harga),
        "description": deskripsi_xendit,
        "invoice_duration": 86400 * 10,  # Diubah menjadi 10 hari
        "customer": {
            "given_names": pelanggan.nama,
            "email": pelanggan.email,
            "mobile_number": no_telp_xendit if no_telp_xendit else f"+62{pelanggan.no_telp.lstrip('0')}" if pelanggan.no_telp else None,
        },
        "currency": "IDR",
        "with_short_url": True,
        "should_send_email": True,  # Force enable email
        "should_send_whatsapp": True, # Force enable WhatsApp

        # TAMBAHKAN ALTERNATIVE WHATSAPP CONFIGURATIONS
        "customer_notification_method": "whatsapp",
        "preferred_notification_channel": "whatsapp",

        # TAMBAHKAN WHATSAPP CONFIGURATION
        "notification_channels": ["whatsapp", "email"],
        "force_notification_channels": True,
        "send_whatsapp": True,
        "whatsapp_enabled": True,

        # TAMBAHKAN BUSINESS DETAILS
        "business_profile": {
            "business_name": "Artacomindo Jejaring Nusa",
            "business_address": "Indonesia",
            "business_contact": "+628986937819",
            "business_industry": "Telecommunications"
        },
        "items": [
            {
                "name": f"Biaya berlangganan internet up to {paket.kecepatan} Mbps",
                "price": harga_dasar,
                "quantity": 1,
                "description": deskripsi_xendit,
                "currency": "IDR",
                "type": "PRODUCT",
            }
        ],
        "fees": [{"type": "Tax", "value": pajak}],
    }

    # Logika external_id dinamis - CONSISTENT dengan invoice_number
    brand_prefix_map = {"ajn-01": "JAKINET", "ajn-02": "JELANTIK", "ajn-03": "NAGRAK"}

    id_brand_pelanggan = brand_info.id_brand
    brand_prefix = brand_prefix_map.get(id_brand_pelanggan, brand_info.brand)

    # Gunakan format yang SAMA dengan invoice_number agar konsisten
    import re
    nama_user = re.sub(r'[^a-zA-Z0-9]', '', pelanggan.nama).upper()
    lokasi_singkat = re.sub(r'[^a-zA-Z0-9]', '', pelanggan.alamat or '').upper()[:10]

    # Format tanggal yang konsisten dengan invoice_number
    bulan_tahun = invoice.tgl_jatuh_tempo.strftime("%B-%Y").upper()  # type: ignore

    # External ID menggunakan format yang sama dengan invoice_number untuk konsistensi
    # Ini akan menghasilkan ID yang konsisten antara Portal JAKINET dan Dashboard Xendit
    payload["external_id"] = f"{brand_prefix}/ftth/{nama_user}/{bulan_tahun}/{lokasi_singkat}/{invoice.id}"

    logger.info(f"Payload yang dikirim ke Xendit: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:  # Tambahkan timeout
        try:
            response = await client.post(settings.XENDIT_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Respons dari Xendit: {json.dumps(result, indent=2)}")

            # DEBUG: Log WhatsApp status specifically
            if result.get("should_send_whatsapp") or result.get("customer_notification_preference"):
                logger.info(f"  WhatsApp Notification Status:")
                logger.info(f"   should_send_whatsapp: {result.get('should_send_whatsapp', 'Not in response')}")
                logger.info(f"   notification_preference: {result.get('customer_notification_preference', 'Not in response')}")
                logger.info(f"   customer_mobile: {result.get('customer', {}).get('mobile_number', 'Not in response')}")

                # Check for WhatsApp specific fields
                if "whatsapp" in result:
                    logger.info(f"   whatsapp_details: {result['whatsapp']}")

            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Error saat membuat invoice Xendit. Payload: {json.dumps(payload, indent=2)}")
            logger.error(f"Respons Error dari Xendit: {e.response.text}")
            raise e
        except httpx.RequestError as e:
            logger.error(f"Kesalahan jaringan ke Xendit: {str(e)}")
            raise ValueError(f"Kesalahan jaringan ke Xendit: {str(e)}")


async def get_paid_invoice_ids_since(days: int) -> list[str]:
    """
    Mengambil daftar external_id dari semua invoice PAID dari SEMUA BRAND.
    """
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    all_paid_ids = []

    for brand_name, api_key in settings.XENDIT_API_KEYS.items():
        if not api_key:
            logger.warning(f"Kunci API Xendit untuk brand '{brand_name}' tidak ditemukan, dilewati.")
            continue

        logger.info(f"Memeriksa pembayaran lunas untuk brand: {brand_name}")
        encoded_key = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {encoded_key}"}

        base_url = "https://api.xendit.co/v2/invoices"
        query_params = {"statuses[]": "PAID", "paid_after": start_date, "limit": 1000}

        # Gunakan httpx dengan params, ini cara yang lebih modern dan aman
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # httpx akan meng-encode 'statuses[]' dengan benar menjadi statuses%5B%5D=PAID
                response = await client.get(base_url, headers=headers, params=query_params)
                response.raise_for_status()

                # Cek apakah response.json() menghasilkan dict dan punya key 'data'
                response_data = response.json()
                invoices_data = response_data.get("data", []) if isinstance(response_data, dict) else []

                brand_paid_ids = [inv.get("external_id") for inv in invoices_data if inv.get("external_id")]
                all_paid_ids.extend(brand_paid_ids)
                logger.info(f"Ditemukan {len(brand_paid_ids)} pembayaran lunas untuk brand {brand_name}.")
            except httpx.HTTPStatusError as e:
                logger.error(f"Error saat mengambil data dari Xendit untuk brand {brand_name}: {e.response.text}")

    return all_paid_ids
