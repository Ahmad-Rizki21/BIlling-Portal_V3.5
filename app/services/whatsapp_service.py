# ====================================================================
# WHATSAPP SERVICE - WasenderAPI Integration
# ====================================================================
# Service ini mengirim pesan WhatsApp menggunakan WasenderAPI
# untuk notifikasi ke pelanggan, khususnya untuk status Suspended
#
# API Documentation: https://wasenderapi.com/whatsapp/
# ====================================================================

import logging
from typing import Optional, Dict, Any
from datetime import date
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Service untuk mengirim pesan WhatsApp melalui WasenderAPI
    """

    # Template pesan untuk berbagai skenario
    TEMPLATES = {
        "suspended_notification": """Halo {nama},

Kami informasikan bahwa layanan internet Anda telah ditangguhkan (Suspended).

Detail Langganan:
- Paket: {paket}
- Alamat: {alamat}
- Status: Suspended

Silakan hubungi admin untuk informasi lebih lanjut dan pembayaran.

Terima kasih.""",

        "payment_reminder": """Halo {nama},

Mohon segera melakukan pembayaran untuk layanan internet Anda.

Detail:
- Nomor Invoice: {invoice}
- Jatuh Tempo: {jatuh_tempo}
- Total: {total}

Pembayaran dapat dilakukan melalui:
- Transfer Bank
- E-Wallet
- Kantor

Terima kasih.""",

        "activation_notification": """Halo {nama},

Selamat! Layanan internet Anda telah aktif.

Detail:
- Paket: {paket}
- Tgl Mulai: {tgl_mulai}

Silakan nikmati layanan internet kami.

Terima kasih.""",
    }

    @staticmethod
    def format_phone_number(phone_number: str) -> str:
        """
        Format phone number ke format international (62 prefix).
        Mengubah nomor yang diawali 0 menjadi 62.
        """
        if not phone_number or phone_number.strip() == '':
            return phone_number

        phone = phone_number.strip()

        # Remove any non-digit characters first
        phone_digits = ''.join(c for c in phone if c.isdigit())

        # If starts with 0, replace with 62
        if phone_digits.startswith('0'):
            return '62' + phone_digits[1:]

        # If already starts with 62 or doesn't start with 0, return as is
        return phone_digits

    @staticmethod
    async def send_message(
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Mengirim pesan WhatsApp melalui WasenderAPI

        Args:
            phone_number: Nomor telepon tujuan (akan diformat otomatis)
            message: Pesan yang akan dikirim

        Returns:
            Dict dengan status success/error dan detail response
        """
        try:
            # Format phone number
            formatted_phone = WhatsAppService.format_phone_number(phone_number)

            if not formatted_phone or len(formatted_phone) < 10:
                return {
                    "success": False,
                    "error": "Nomor telepon tidak valid",
                    "phone_number": phone_number
                }

            # Prepare request
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "to": formatted_phone,
                "text": message
            }

            # Send request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.WHATSAPP_API_URL,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"WhatsApp sent successfully to {formatted_phone}")
                    return {
                        "success": True,
                        "data": result,
                        "phone_number": formatted_phone
                    }
                else:
                    error_detail = response.text
                    logger.error(f"WhatsApp API error: {response.status_code} - {error_detail}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "detail": error_detail,
                        "phone_number": formatted_phone
                    }

        except httpx.TimeoutException:
            logger.error("WhatsApp API timeout")
            return {
                "success": False,
                "error": "Timeout - API tidak merespon",
                "phone_number": phone_number
            }
        except Exception as e:
            logger.error(f"WhatsApp service error: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    @staticmethod
    async def send_suspended_notification(
        nama: str,
        phone_number: str,
        paket: str,
        alamat: str
    ) -> Dict[str, Any]:
        """
        Mengirim notifikasi Suspended ke pelanggan

        Args:
            nama: Nama pelanggan
            phone_number: Nomor telepon pelanggan
            paket: Nama paket layanan
            alamat: Alamat pelanggan

        Returns:
            Dict dengan status success/error
        """
        message = WhatsAppService.TEMPLATES["suspended_notification"].format(
            nama=nama,
            paket=paket,
            alamat=alamat
        )

        return await WhatsAppService.send_message(phone_number, message)

    @staticmethod
    async def send_payment_reminder(
        nama: str,
        phone_number: str,
        invoice: str,
        jatuh_tempo: str,
        total: str
    ) -> Dict[str, Any]:
        """
        Mengirim reminder pembayaran ke pelanggan

        Args:
            nama: Nama pelanggan
            phone_number: Nomor telepon pelanggan
            invoice: Nomor invoice
            jatuh_tempo: Tanggal jatuh tempo
            total: Total tagihan

        Returns:
            Dict dengan status success/error
        """
        message = WhatsAppService.TEMPLATES["payment_reminder"].format(
            nama=nama,
            invoice=invoice,
            jatuh_tempo=jatuh_tempo,
            total=total
        )

        return await WhatsAppService.send_message(phone_number, message)

    @staticmethod
    async def send_activation_notification(
        nama: str,
        phone_number: str,
        paket: str,
        tgl_mulai: date
    ) -> Dict[str, Any]:
        """
        Mengirim notifikasi aktivasi layanan ke pelanggan

        Args:
            nama: Nama pelanggan
            phone_number: Nomor telepon pelanggan
            paket: Nama paket layanan
            tgl_mulai: Tanggal mulai langganan

        Returns:
            Dict dengan status success/error
        """
        message = WhatsAppService.TEMPLATES["activation_notification"].format(
            nama=nama,
            paket=paket,
            tgl_mulai=tgl_mulai.strftime('%d/%m/%Y')
        )

        return await WhatsAppService.send_message(phone_number, message)

    @staticmethod
    async def send_custom_message(
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Mengirim pesan custom ke pelanggan

        Args:
            phone_number: Nomor telepon pelanggan
            message: Pesan custom

        Returns:
            Dict dengan status success/error
        """
        return await WhatsAppService.send_message(phone_number, message)
