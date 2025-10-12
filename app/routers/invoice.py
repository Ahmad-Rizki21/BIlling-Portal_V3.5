from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy import func, or_
from datetime import date, timedelta, datetime, timezone
from dateutil.relativedelta import relativedelta
import uuid
from typing import List, Optional
import json
import logging
import pytz
from ..websocket_manager import manager
import math
from sqlalchemy import and_

from typing import Optional

# Impor semua model dan skema yang dibutuhkan
from ..auth import has_permission
from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..schemas.invoice import (
    Invoice as InvoiceSchema,
    InvoiceGenerate,
    MarkAsPaidRequest,
)
from ..database import get_db
from sqlalchemy import select, func
from ..services import mikrotik_service
from ..config import settings
from ..services import xendit_service, mikrotik_service

logger = logging.getLogger("app.routers.invoice")

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[InvoiceSchema])
async def get_all_invoices(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = None,
    status_invoice: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,  # <-- TAMBAHKAN INI
    limit: Optional[int] = None,  # <-- TAMBAHKAN INI
):
    """Mengambil semua data invoice dengan filter."""
    query = (
        select(InvoiceModel).join(InvoiceModel.pelanggan)
        # PERBAIKAN: Eager load relasi turunan untuk mencegah N+1 query
        # saat skema respons membutuhkan data dari relasi ini (misal: nama brand).
        .options(selectinload(InvoiceModel.pelanggan).selectinload(PelangganModel.harga_layanan))
    )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                InvoiceModel.invoice_number.ilike(search_term),
                PelangganModel.nama.ilike(search_term),
                InvoiceModel.id_pelanggan.ilike(search_term),
            )
        )

    if status_invoice:
        query = query.where(InvoiceModel.status_invoice == status_invoice)

    if start_date:
        query = query.where(InvoiceModel.tgl_jatuh_tempo >= start_date)
    if end_date:
        query = query.where(InvoiceModel.tgl_jatuh_tempo <= end_date)

    # Terapkan paginasi setelah semua filter
    if limit is not None:
        query = query.offset(skip).limit(limit)
    # ---------------------------

    result = await db.execute(query)
    return result.scalars().all()


def parse_xendit_datetime(iso_datetime_str: str) -> datetime:
    """Fungsi untuk mengkonversi format datetime ISO 8601 dari Xendit."""
    try:
        if not iso_datetime_str:
            return datetime.now(pytz.utc)
        if iso_datetime_str.endswith("Z"):
            iso_datetime_str = iso_datetime_str[:-1] + "+00:00"
        return datetime.fromisoformat(iso_datetime_str)
    except (ValueError, TypeError):
        return datetime.now(pytz.utc)


async def _process_successful_payment(db: AsyncSession, invoice: InvoiceModel, payload: dict = None):
    """Fungsi terpusat untuk menangani logika setelah invoice lunas."""

    pelanggan = invoice.pelanggan
    if not pelanggan or not pelanggan.langganan:
        logger.error(f"Pelanggan atau langganan tidak ditemukan untuk invoice {invoice.invoice_number}")
        return

    langganan = pelanggan.langganan[0]

    # Cek apakah langganan sebelumnya berstatus 'Suspended'
    is_suspended_or_inactive = langganan.status == "Suspended" or not langganan.status

    # Update status invoice (tetap)
    invoice.status_invoice = "Lunas"
    if payload:
        invoice.paid_amount = float(payload.get("paid_amount", invoice.total_harga))
        invoice.paid_at = parse_xendit_datetime(payload.get("paid_at"))
    else:
        invoice.paid_amount = invoice.total_harga
        invoice.paid_at = datetime.now(timezone.utc)

    db.add(invoice)

    next_due_date = None

    if langganan.metode_pembayaran == "Prorate":
        paket = langganan.paket_layanan
        brand = pelanggan.harga_layanan
        langganan.metode_pembayaran = "Otomatis"
        current_due_date = invoice.tgl_jatuh_tempo

        if not paket or not brand:
            logger.error(f"Data paket/brand tidak lengkap untuk langganan ID {langganan.id}")
            # Set fallback jika data tidak ada, agar tidak crash
            next_due_date = (current_due_date + relativedelta(months=1)).replace(day=1)
        else:
            # Hitung harga normal penuh sebagai pembanding
            harga_paket = float(paket.harga)
            pajak_persen = float(brand.pajak)
            harga_normal_full = harga_paket * (1 + (pajak_persen / 100))

            # Logika Pembeda: Apakah ini tagihan prorate biasa atau gabungan?
            if invoice.total_harga > (harga_normal_full + 1):
                # Skenario 1: INI ADALAH TAGIHAN GABUNGAN
                next_due_date = (current_due_date + relativedelta(months=2)).replace(day=1)
                logger.info(f"Tagihan gabungan terdeteksi. Jatuh tempo berikutnya diatur ke {next_due_date}")
            else:
                # Skenario 2: INI ADALAH TAGIHAN PRORATE BIASA
                next_due_date = (current_due_date + relativedelta(months=1)).replace(day=1)
                logger.info(f"Tagihan prorate biasa terdeteksi. Jatuh tempo berikutnya diatur ke {next_due_date}")

            # Reset harga langganan ke harga normal untuk bulan-bulan berikutnya
            langganan.harga_awal = round(harga_normal_full, 0)

    else:  # Skenario 3: Jika sudah Otomatis (PEMBAYARAN BULANAN NORMAL)
        current_due_date = langganan.tgl_jatuh_tempo or date.today()
        # Jatuh tempo berikutnya adalah 1 bulan dari sekarang
        next_due_date = (current_due_date + relativedelta(months=1)).replace(day=1)

    # Update langganan (tidak berubah)
    langganan.status = "Aktif"
    langganan.tgl_jatuh_tempo = next_due_date
    langganan.tgl_invoice_terakhir = date.today()
    db.add(langganan)

    # HANYA trigger update Mikrotik jika status sebelumnya adalah 'Suspended'
    if is_suspended_or_inactive:
        data_teknis = pelanggan.data_teknis
        if not data_teknis:
            logger.error(f"Data Teknis tidak ditemukan untuk pelanggan ID {pelanggan.id}. Mikrotik update dilewati.")
        else:
            try:
                # Panggil fungsi dengan SEMUA argumen yang dibutuhkan
                await mikrotik_service.trigger_mikrotik_update(
                    db,
                    langganan,
                    data_teknis,
                    data_teknis.id_pelanggan,  # old_id_pelanggan diisi dengan id saat ini
                )
                logger.info(f"Berhasil trigger re-aktivasi Mikrotik untuk langganan ID {langganan.id}")

                # Jika berhasil, set flag pending sync (jika ada) kembali ke False
                if data_teknis.mikrotik_sync_pending:
                    data_teknis.mikrotik_sync_pending = False
                    db.add(data_teknis)

            except Exception as e:
                # Jika GAGAL, catat error DAN set flag retry menjadi True
                logger.error(
                    f"Gagal trigger re-aktivasi Mikrotik untuk langganan ID {langganan.id}: {e}. Menandai untuk dicoba lagi."
                )
                data_teknis.mikrotik_sync_pending = True
                db.add(data_teknis)
    else:
        logger.info(f"Langganan ID {langganan.id} sudah Aktif. Mikrotik update dilewati.")

    # Notif ke frontend
    try:
        target_roles = ["Admin", "NOC", "Finance"]
        query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name).in_([r.lower() for r in target_roles]))
        result = await db.execute(query)
        target_user_ids = result.scalars().all()

        if target_user_ids:
            # Pastikan pelanggan sudah di-load dengan benar
            pelanggan_nama = pelanggan.nama if pelanggan else "N/A"
            notification_payload = {
                "type": "new_payment",
                "data": {
                    "invoice_number": invoice.invoice_number,
                    "pelanggan_nama": pelanggan_nama,
                    "message": f"Pembayaran untuk invoice {invoice.invoice_number} dari {pelanggan_nama} telah diterima.",
                },
            }
            # Tambahkan log ini untuk memastikan user ID ditemukan
            logger.info(f"Mencoba mengirim notifikasi pembayaran ke user IDs: {target_user_ids}")
            await manager.broadcast_to_roles(notification_payload, target_user_ids)
            logger.info(f"Notifikasi pembayaran berhasil dikirim untuk invoice {invoice.invoice_number}")
        else:
            logger.warning(f"Tidak ada user dengan role Admin/CS yang ditemukan untuk dikirimi notifikasi.")

    except Exception as e:
        logger.error(f"Gagal mengirim notifikasi pembayaran untuk invoice {invoice.invoice_number}: {e}")

    logger.info(f"Payment processed successfully for invoice {invoice.invoice_number}")


# @router.post("/xendit-callback", status_code=status.HTTP_200_OK)
# async def handle_xendit_callback(
#     request: Request,
#     x_callback_token: Optional[str] = Header(None),
#     db: AsyncSession = Depends(get_db),
# ):
#     payload = await request.json()
#     logger.info(f"Xendit callback received. Payload: {json.dumps(payload, indent=2)}")

#     external_id = payload.get("external_id")
#     if not external_id:
#         raise HTTPException(
#             status_code=400, detail="External ID tidak ditemukan di payload"
#         )

#     try:
#         brand_prefix = external_id.split("/")[0]
#     except IndexError:
#         raise HTTPException(status_code=400, detail="Format external_id tidak valid")

#     correct_token = None
#     if brand_prefix.lower() in ["jakinet", "nagrak"]:
#         correct_token = settings.XENDIT_CALLBACK_TOKENS.get("ARTACOM")
#         logger.info("Validating with ARTACOM callback token.")
#     elif brand_prefix.lower() == "jelantik":
#         correct_token = settings.XENDIT_CALLBACK_TOKENS.get("JELANTIK")
#         logger.info("Validating with JELANTIK callback token.")

#     if not correct_token or x_callback_token != correct_token:
#         logger.warning(f"Invalid callback token received for brand '{brand_prefix}'.")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback token"
#         )


@router.post("/xendit-callback", status_code=status.HTTP_200_OK)
async def handle_xendit_callback(
    request: Request,
    x_callback_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()
    logger.info(f"Xendit callback received. Payload: {json.dumps(payload, indent=2)}")

    external_id = payload.get("external_id")
    if not external_id:
        raise HTTPException(status_code=400, detail="External ID tidak ditemukan di payload")

    brand_prefix = None
    try:
        if "/" in external_id:
            brand_prefix = external_id.split("/")[0]
        # Untuk webhook test, tidak ada prefix brand. Kita validasi token saja
    except IndexError:
        raise HTTPException(status_code=400, detail="Format external_id tidak valid")

    # VALIDASI TOKEN SECARA LANGSUNG
    # 1. Coba validasi dengan token ARTACOMINDO (Jakinet, Nagrak)
    artacom_token = settings.XENDIT_CALLBACK_TOKENS.get("ARTACOMINDO")
    if artacom_token and x_callback_token == artacom_token:
        logger.info("Validating with ARTACOMINDO callback token.")
        # Cek apakah brand_prefix (jika ada) sesuai dengan token ini
        if brand_prefix and brand_prefix.lower() not in [
            "jakinet",
            "nagrak",
            "artacom",
        ]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid brand for this token",
            )
        correct_token = artacom_token

    # 2. Coba validasi dengan token JELANTIK
    jelantik_token = settings.XENDIT_CALLBACK_TOKENS.get("JELANTIK")
    if jelantik_token and x_callback_token == jelantik_token:
        logger.info("Validating with JELANTIK callback token.")
        # Cek apakah brand_prefix (jika ada) sesuai dengan token ini
        if brand_prefix and brand_prefix.lower() != "jelantik":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid brand for this token",
            )
        correct_token = jelantik_token

    # Jika tidak ada token yang cocok, kembalikan 401
    if not correct_token:
        logger.warning("Invalid callback token received.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback token")
    xendit_status = payload.get("status")

    # PERBAIKAN: Eager load semua relasi yang dibutuhkan oleh _process_successful_payment
    # untuk menghindari N+1 query dan membuat proses lebih efisien.
    stmt = (
        select(InvoiceModel)
        .where(InvoiceModel.xendit_external_id == external_id)
        .options(
            selectinload(InvoiceModel.pelanggan).options(
                selectinload(PelangganModel.harga_layanan),
                selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                selectinload(PelangganModel.data_teknis),
            )
        )
    )
    invoice = (await db.execute(stmt)).scalar_one_or_none()

    if not invoice:
        logger.warning(f"Invoice with external_id {external_id} not found, but callback is valid.")
        return {"message": "Callback valid, invoice not found."}

    if invoice.status_invoice == "Lunas":
        return {"message": "Invoice already processed"}

    try:
        if xendit_status == "PAID":
            await _process_successful_payment(db, invoice, payload)

        elif xendit_status == "EXPIRED":
            invoice.status_invoice = "Kadaluarsa"
            db.add(invoice)

        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing Xendit callback for external_id {external_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while processing callback.")

    return {"message": "Callback processed successfully"}


@router.post(
    "/generate",
    response_model=InvoiceSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission("create_invoices"))],
)
async def generate_manual_invoice(invoice_data: InvoiceGenerate, db: AsyncSession = Depends(get_db)):
    """Membuat satu invoice secara manual berdasarkan langganan_id."""
    langganan = await db.get(
        LanggananModel,
        invoice_data.langganan_id,
        options=[
            selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis),
            selectinload(LanggananModel.paket_layanan),
        ],
    )
    if not langganan:
        raise HTTPException(status_code=404, detail="Langganan tidak ditemukan")

    if langganan.status == "Berhenti":
        raise HTTPException(
            status_code=400,
            detail=f"Gagal membuat invoice. Status langganan untuk pelanggan '{langganan.pelanggan.nama}' adalah 'Berhenti'.",
        )

    pelanggan = langganan.pelanggan
    paket = langganan.paket_layanan
    if not pelanggan or not paket or not pelanggan.harga_layanan or not pelanggan.data_teknis:
        raise HTTPException(
            status_code=400,
            detail=f"Data pendukung (pelanggan, paket, brand, teknis) tidak lengkap untuk langganan ID {langganan.id}",
        )

    brand = pelanggan.harga_layanan
    data_teknis = pelanggan.data_teknis

    if not paket.harga or not brand.pajak:
        raise HTTPException(status_code=400, detail="Harga paket atau pajak tidak valid")

    existing_invoice_stmt = select(InvoiceModel.id).where(
        InvoiceModel.pelanggan_id == langganan.pelanggan_id,
        InvoiceModel.tgl_jatuh_tempo == langganan.tgl_jatuh_tempo,
    )
    if (await db.execute(existing_invoice_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Invoice untuk periode ini sudah ada.")

    jatuh_tempo_str = langganan.tgl_jatuh_tempo.strftime("%d/%m/%Y")
    nomor_invoice = (
        f"INV-{pelanggan.nama.replace(' ', '')}-{langganan.tgl_jatuh_tempo.strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    )

    # Ambil total harga langsung dari data langganan yang sudah dihitung (prorate + PPN).
    total_harga = float(langganan.harga_awal)
    pajak_persen = float(brand.pajak)

    # Karena Xendit butuh nilai pajak terpisah, kita hitung mundur dari total harga.
    # 1. Cari harga dasar sebelum pajak.
    harga_dasar = total_harga / (1 + (pajak_persen / 100))

    # 2. Hitung nilai pajak berdasarkan selisih total harga dan harga dasar.
    # Gunakan pembulatan untuk konsistensi.
    pajak = round(total_harga - harga_dasar)

    # Pastikan harga dasar untuk item di Xendit juga konsisten.
    harga_dasar = total_harga - pajak

    new_invoice_data = {
        "invoice_number": nomor_invoice,
        "pelanggan_id": pelanggan.id,
        "id_pelanggan": data_teknis.id_pelanggan,
        "brand": brand.brand,
        "total_harga": total_harga,
        "no_telp": pelanggan.no_telp,
        "email": pelanggan.email,
        "tgl_invoice": date.today(),
        "tgl_jatuh_tempo": langganan.tgl_jatuh_tempo,
        "status_invoice": "Belum Dibayar",
    }

    db_invoice = InvoiceModel(**new_invoice_data)
    db.add(db_invoice)
    await db.flush()

    try:
        deskripsi_xendit = ""
        jatuh_tempo_str_lengkap = db_invoice.tgl_jatuh_tempo.strftime("%d/%m/%Y")

        if langganan.metode_pembayaran == "Prorate":

            # Hitung harga normal untuk perbandingan
            harga_normal_full = float(paket.harga) * (1 + (float(brand.pajak) / 100))

            # Cek apakah ini invoice gabungan
            if db_invoice.total_harga > (harga_normal_full + 1):
                # INI TAGIHAN GABUNGAN
                start_day = db_invoice.tgl_invoice.day
                end_day = db_invoice.tgl_jatuh_tempo.day
                periode_prorate_str = db_invoice.tgl_jatuh_tempo.strftime("%B %Y")
                periode_berikutnya_str = (db_invoice.tgl_jatuh_tempo + relativedelta(months=1)).strftime("%B %Y")

                deskripsi_xendit = (
                    f"Biaya internet up to {paket.kecepatan} Mbps. "
                    f"Periode Prorate {start_day}-{end_day} {periode_prorate_str} + "
                    f"Periode {periode_berikutnya_str}"
                )
            else:
                # INI TAGIHAN PRORATE BIASA
                start_day = db_invoice.tgl_invoice.day
                end_day = db_invoice.tgl_jatuh_tempo.day
                periode_str = db_invoice.tgl_jatuh_tempo.strftime("%B %Y")
                deskripsi_xendit = (
                    f"Biaya berlangganan internet up to {paket.kecepatan} Mbps, "
                    f"Periode Tgl {start_day}-{end_day} {periode_str}"
                )

        else:  # Otomatis
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps "
                f"jatuh tempo pembayaran tanggal {jatuh_tempo_str_lengkap}"
            )

        no_telp_xendit = (
            # PERBAIKAN: Gunakan lstrip untuk menghapus '0' di awal dengan aman.
            f"+62{pelanggan.no_telp.lstrip('0')}"
            if pelanggan.no_telp and pelanggan.no_telp.startswith("0")
            else pelanggan.no_telp
        )

        # Kirim deskripsi yang sudah dinamis ke Xendit
        xendit_response = await xendit_service.create_xendit_invoice(
            db_invoice, pelanggan, paket, deskripsi_xendit, pajak, no_telp_xendit
        )

        db_invoice.payment_link = xendit_response.get("short_url", xendit_response.get("invoice_url"))
        db_invoice.xendit_id = xendit_response.get("id")
        db_invoice.xendit_external_id = xendit_response.get("external_id")
        await db.commit()
        await db.refresh(db_invoice)
    except Exception as e:
        await db.rollback()
        logger.error(f"Gagal membuat invoice di Xendit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal membuat invoice di Xendit: {str(e)}")

    return db_invoice


@router.post(
    "/{invoice_id}/mark-as-paid",
    response_model=InvoiceSchema,
    dependencies=[Depends(has_permission("edit_invoices"))],
)
async def mark_invoice_as_paid(invoice_id: int, payload: MarkAsPaidRequest, db: AsyncSession = Depends(get_db)):
    """Menandai sebuah invoice sebagai lunas secara manual."""
    # PERBAIKAN: Eager load semua relasi yang dibutuhkan oleh _process_successful_payment
    # untuk menghindari N+1 query dan membuat proses lebih efisien.
    stmt = (
        select(InvoiceModel)
        .where(InvoiceModel.id == invoice_id)
        .options(
            selectinload(InvoiceModel.pelanggan).options(
                selectinload(PelangganModel.harga_layanan),
                selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                selectinload(PelangganModel.data_teknis),
            )
        )
    )
    invoice = (await db.execute(stmt)).scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")

    if invoice.status_invoice == "Lunas":
        raise HTTPException(status_code=400, detail="Invoice ini sudah lunas.")

    invoice.metode_pembayaran = payload.metode_pembayaran

    await _process_successful_payment(db, invoice)

    await db.commit()
    await db.refresh(invoice)

    logger.info(f"Invoice {invoice.invoice_number} ditandai lunas secara manual via {payload.metode_pembayaran}")

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(has_permission("delete_invoices"))],
)
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Menghapus satu invoice berdasarkan ID-nya."""

    db_invoice = await db.get(InvoiceModel, invoice_id)

    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")

    await db.delete(db_invoice)
    await db.commit()

    return None


# Logic atau EndPoint untuk melihat Status Invoice itu masih layar atau sudah kadaluarsa ??


@router.post(
    "/internal/update-overdue-status",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_overdue_invoices(db: AsyncSession = Depends(get_db)):
    """
    Endpoint internal untuk memperbarui status invoice menjadi 'Kadaluarsa' dan men-suspend layanan.
    Endpoint ini HARUS dipanggil oleh scheduler (cron job) setiap hari dan tidak boleh terekspos ke publik.
    `include_in_schema=False` digunakan agar tidak muncul di dokumentasi API publik.
    """
    today = date.today()
    # Aturan: Kadaluarsa jika hari ini adalah hari ke-6 setelah jatuh tempo (lewat 5 hari).
    overdue_threshold_date = today - timedelta(days=5)

    logger = logging.getLogger("app.routers.invoice")
    logger.info("Scheduler-triggered job: Mencari invoice kadaluarsa...")

    # 1. Cari semua invoice yang 'Belum Dibayar' dan sudah melewati masa tenggang
    stmt = (
        select(InvoiceModel)
        # PERBAIKAN: Eager load data_teknis untuk mencegah N+1 query di dalam loop.
        .options(
            selectinload(InvoiceModel.pelanggan).options(
                selectinload(PelangganModel.langganan),
                selectinload(PelangganModel.data_teknis),
            )
        ).where(
            and_(
                InvoiceModel.status_invoice == "Belum Dibayar",
                InvoiceModel.tgl_jatuh_tempo < overdue_threshold_date,
            )
        )
    )

    overdue_invoices = (await db.execute(stmt)).scalars().all()

    if not overdue_invoices:
        logger.info("Tidak ada invoice kadaluarsa yang perlu diperbarui.")
        return {"message": "Tidak ada invoice kadaluarsa yang perlu diperbarui."}

    updated_count = 0
    suspended_count = 0
    # 2. Update status dan suspend layanan untuk setiap invoice yang ditemukan
    for invoice in overdue_invoices:
        invoice.status_invoice = "Kadaluarsa"
        db.add(invoice)
        updated_count += 1

        # Logika untuk men-suspend layanan pelanggan
        try:
            pelanggan = invoice.pelanggan
            if pelanggan and pelanggan.langganan:
                langganan_pelanggan = pelanggan.langganan[0]
                if langganan_pelanggan.status != "Suspended":
                    langganan_pelanggan.status = "Suspended"
                    db.add(langganan_pelanggan)

                    # PERBAIKAN: Panggil trigger_mikrotik_update dengan argumen yang benar.
                    data_teknis = pelanggan.data_teknis
                    if data_teknis:
                        await mikrotik_service.trigger_mikrotik_update(
                            db,
                            langganan_pelanggan,
                            data_teknis,
                            data_teknis.id_pelanggan,
                        )
                        suspended_count += 1
                        logger.info(f"Layanan untuk {pelanggan.nama} (Invoice: {invoice.invoice_number}) telah di-suspend.")
                    else:
                        logger.error(
                            f"Data Teknis tidak ditemukan untuk pelanggan {pelanggan.nama}, suspend di Mikrotik dilewati."
                        )
        except Exception as e:
            logger.error(f"Gagal men-suspend layanan untuk invoice {invoice.invoice_number}: {e}")

    await db.commit()

    message = f"Proses selesai. {updated_count} invoice diperbarui menjadi 'Kadaluarsa'. {suspended_count} layanan di-suspend."
    logger.info(message)
    return {"message": message}
