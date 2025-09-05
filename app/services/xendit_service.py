# app/services/xendit_service.py

import httpx
from ..config import settings
from ..models import Invoice, Pelanggan, PaketLayanan
import os
from dateutil.relativedelta import relativedelta
import base64
import logging
import urllib.parse
import json
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("app.services.xendit")


async def create_xendit_invoice(
    invoice: Invoice,
    pelanggan: Pelanggan,
    paket: PaketLayanan,
    deskripsi_xendit: str,
    pajak: float,
    no_telp_xendit: str = None,
) -> dict:
    """Mengirim request ke Xendit untuk membuat invoice baru."""
    target_key_name = pelanggan.harga_layanan.xendit_key_name
    api_key = settings.XENDIT_API_KEYS.get(target_key_name)
    if not api_key:
        raise ValueError(f"Kunci API Xendit untuk '{target_key_name}' tidak ditemukan.")

    encoded_key = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_key}",
    }

    brand_info = pelanggan.harga_layanan
    jatuh_tempo_str = invoice.tgl_jatuh_tempo.strftime("%d/%m/%Y")

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
            "mobile_number": no_telp_xendit if no_telp_xendit else pelanggan.no_telp,
        },
        "currency": "IDR",
        "with_short_url": True,
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

    # Logika external_id dinamis
    brand_prefix_map = {"ajn-01": "Jakinet", "ajn-02": "Jelantik", "ajn-03": "Nagrak"}

    id_brand_pelanggan = brand_info.id_brand
    brand_prefix = brand_prefix_map.get(id_brand_pelanggan, brand_info.brand)
    nama_user = pelanggan.nama.replace(" ", "")
    lokasi_singkat = pelanggan.alamat.split(" ")[0] if pelanggan.alamat else "Lokasi"

    # ▼▼▼ PERBAIKAN DI SINI ▼▼▼
    # Langsung format tanggal jatuh tempo dari invoice tanpa menambahkan bulan
    bulan_tahun = invoice.tgl_jatuh_tempo.strftime("%B-%Y")

    payload["external_id"] = (
        f"{brand_prefix}/ftth/{nama_user}/{bulan_tahun}/{lokasi_singkat}/{invoice.id}"
    )
    # bulan_tahun = invoice.tgl_jatuh_tempo.strftime('%B-%Y')
    # payload["external_id"] = f"{brand_prefix}/ftth/{nama_user}/{bulan_tahun}/{invoice.id}"

    logger.info(f"Payload yang dikirim ke Xendit: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:  # Tambahkan timeout
        try:
            response = await client.post(
                settings.XENDIT_API_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Respons dari Xendit: {json.dumps(result, indent=2)}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error saat membuat invoice Xendit. Payload: {json.dumps(payload, indent=2)}"
            )
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
            logger.warning(
                f"Kunci API Xendit untuk brand '{brand_name}' tidak ditemukan, dilewati."
            )
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
                response = await client.get(
                    base_url, headers=headers, params=query_params
                )
                response.raise_for_status()

                # Cek apakah response.json() menghasilkan dict dan punya key 'data'
                response_data = response.json()
                invoices_data = (
                    response_data.get("data", [])
                    if isinstance(response_data, dict)
                    else []
                )

                brand_paid_ids = [
                    inv.get("external_id")
                    for inv in invoices_data
                    if inv.get("external_id")
                ]
                all_paid_ids.extend(brand_paid_ids)
                logger.info(
                    f"Ditemukan {len(brand_paid_ids)} pembayaran lunas untuk brand {brand_name}."
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Error saat mengambil data dari Xendit untuk brand {brand_name}: {e.response.text}"
                )

    return all_paid_ids
