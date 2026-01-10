"""
Skrip untuk memindahkan invoice lama ke tabel arsip.

Skrip ini mencari invoice yang:
- Berstatus 'Lunas', 'Kadaluarsa', atau 'Batal'
- Tanggal pembuatan (`created_at`) atau tanggal jatuh tempo (`tgl_jatuh_tempo`) lebih lama dari `months_threshold` bulan.

Lalu memindahkannya dari tabel `invoices` ke `invoices_archive`.
"""
import asyncio
import logging
import sys
import os

# Menambahkan path root proyek ke sys.path agar impor absolut bisa bekerja
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.invoice import Invoice
from app.models.invoice_archive import InvoiceArchive

# Setup logger
logger = logging.getLogger("app.archive_job")
logger.setLevel(logging.INFO)
# Menambahkan handler jika belum ada
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


async def archive_old_invoices(months_threshold: int = 12, dry_run: bool = False):
    """
    Memindahkan invoice lama ke tabel arsip.

    Args:
        months_threshold (int): Ambang batas bulan. Invoice yang lebih lama dari
                                ini (berdasarkan created_at atau tgl_jatuh_tempo)
                                akan diarsipkan. Default 12 bulan.
        dry_run (bool): Jika True, hanya preview data yang akan diarsipkan tanpa eksekusi.
    """
    mode = "DRY RUN (Preview)" if dry_run else "LIVE EXECUTION"
    logger.info(f"Mode: {mode}")
    logger.info(f"Memulai proses arsip invoice lebih lama dari {months_threshold} bulan...")

    # Hitung tanggal cutoff
    cutoff_date = datetime.now() - timedelta(days=months_threshold * 30) # Aproksimasi 30 hari per bulan
    cutoff_date_only = cutoff_date.date()
    logger.info(f"Tanggal cutoff: {cutoff_date_only} (invoice dengan tgl_jatuh_tempo < tanggal ini akan diarsipkan)")

    # Status invoice yang dianggap sebagai historis
    historical_statuses = ["Lunas", "Kadaluarsa", "Batal"]

    async with AsyncSessionLocal() as db:
        try:
            # Ambil invoice lama yang memenuhi kriteria
            stmt = (
                select(Invoice)
                .where(
                    Invoice.status_invoice.in_(historical_statuses),
                    # Gunakan tgl_jatuh_tempo atau created_at untuk menentukan usia
                    # Kita bisa menggunakan min(tgl_jatuh_tempo, created_at) tetapi lebih sederhana gunakan salah satu
                    # Kita gunakan tgl_jatuh_tempo karena merepresentasikan periode tagihan
                    Invoice.tgl_jatuh_tempo < cutoff_date_only
                    # Atau gunakan Invoice.created_at jika lebih sesuai:
                    # Invoice.created_at < cutoff_date
                )
                # .options(selectinload(Invoice.pelanggan)) # Jika relasi perlu dimuat, biasanya tidak perlu untuk arsip
            )

            result = await db.execute(stmt)
            old_invoices = result.scalars().all()

            if not old_invoices:
                logger.info("Tidak ditemukan invoice yang memenuhi kriteria arsip.")
                return

            logger.info(f"Ditemukan {len(old_invoices)} invoice untuk diarsipkan.")

            # DRY RUN: Tampilkan preview tanpa eksekusi
            if dry_run:
                logger.info("=" * 80)
                logger.info("PREVIEW - Data yang akan diarsipkan:")
                logger.info("=" * 80)

                # Statistik berdasarkan status
                status_count = {}
                # Statistik berdasarkan bulan
                month_count = {}

                for inv in old_invoices[:50]:  # Tampilkan max 50 sample
                    status = inv.status_invoice or "Unknown"
                    status_count[status] = status_count.get(status, 0) + 1

                    # Bulan dari tgl_jatuh_tempo
                    if inv.tgl_jatuh_tempo:
                        month_key = inv.tgl_jatuh_tempo.strftime("%Y-%m")
                        month_count[month_key] = month_count.get(month_key, 0) + 1

                logger.info(f"Total invoice yang akan diarsipkan: {len(old_invoices)}")
                logger.info(f"Breakdown by Status: {status_count}")
                logger.info(f"Breakdown by Month (tgl_jatuh_tempo): {month_count}")

                # Tampilkan 10 sample pertama
                logger.info("\nSample 10 invoice pertama:")
                for i, inv in enumerate(old_invoices[:10], 1):
                    logger.info(f"  {i}. {inv.invoice_number} | {inv.status_invoice} | Tgl: {inv.tgl_jatuh_tempo} | Rp{inv.total_harga:,.0f}")

                logger.info("=" * 80)
                logger.info("DRY RUN SELESAI - Tidak ada perubahan yang dilakukan.")
                logger.info("=" * 80)
                return

            # Pindahkan ke arsip
            archived_count = 0
            failed_to_archive = 0 # Counter untuk item yang gagal diarsipkan
            for inv in old_invoices:
                try:
                    # Buat instance InvoiceArchive dari Invoice
                    # Gunakan to_dict dan hapus 'id' agar tidak konflik dengan auto-increment di arsip
                    inv_dict = inv.to_dict()
                    # Hapus 'id' agar tidak konflik saat insert ke tabel arsip (ID baru akan di-generate)
                    inv_dict.pop('id', None) # Hapus ID asli
                    inv_dict.pop('deleted_at', None) # Hapus deleted_at karena belum ada di tabel arsip
                    # Kita tetap menyertakan deleted_at, karena sekarang sudah ada di InvoiceArchive
                    archive_inv = InvoiceArchive(**inv_dict)

                    # Menambahkan ke sesi arsip
                    db.add(archive_inv)
                    archived_count += 1
                except Exception as e:
                    # Log error dan rollback untuk iterasi ini
                    logger.error(f"Gagal mengarsipkan invoice ID {inv.id} (Number: {inv.invoice_number}): {e}")
                    failed_to_archive += 1
                    # Lanjutkan ke invoice berikutnya, jangan rollback keseluruhan proses
                    continue

            if archived_count > 0:
                try:
                    # Commit dulu untuk menyimpan arsip
                    await db.commit()
                    logger.info(f"Berhasil menyimpan {archived_count} invoice ke tabel arsip.")
                except Exception as e:
                    await db.rollback()
                    logger.error(f"Commit ke tabel arsip gagal: {e}")
                    # Karena data arsip gagal disimpan, kita tidak boleh menghapus dari tabel utama
                    # Kita raise error agar proses penghapusan dibatalkan
                    raise
            else:
                logger.info("Tidak ada invoice yang berhasil dipersiapkan untuk arsip.")

            if failed_to_archive > 0:
                logger.warning(f"Peringatan: {failed_to_archive} invoice gagal diarsipkan dan akan dilewati.")
                # Kita bisa pilih untuk tetap melanjutkan atau berhenti di sini tergantung kebijakan
                # Untuk saat ini, kita lanjutkan, tapi log peringatan

            # Hapus dari tabel utama
            # Ambil ID dari invoice yang sudah diproses untuk dihapus
            ids_to_delete = [inv.id for inv in old_invoices]
            if ids_to_delete:
                delete_stmt = delete(Invoice).where(Invoice.id.in_(ids_to_delete))
                await db.execute(delete_stmt)
                await db.commit()
                logger.info(f"Berhasil menghapus {len(ids_to_delete)} invoice dari tabel utama.")

        except Exception as e:
            await db.rollback()
            logger.error(f"Terjadi kesalahan saat mengarsipkan invoice: {e}")
            raise # Re-raise agar caller tahu ada error


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Arsipkan invoice lama ke tabel invoices_archive')
    parser.add_argument('months', type=int, nargs='?', default=12,
                        help='Ambang batas bulan (default: 12)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview data yang akan diarsipkan tanpa eksekusi (recommended sebelum run beneran)')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"ARCHIVE INVOICE JOB")
    print(f"{'='*80}")
    print(f"Bulan threshold: {args.months}")
    print(f"Mode: {'DRY RUN (Preview)' if args.dry_run else 'LIVE EXECUTION - Akan mengubah database!'}")
    print(f"{'='*80}\n")

    if not args.dry_run:
        confirm = input("⚠️  WARNING: Ini akan memindahkan invoice ke arsip dan menghapus dari tabel utama!\n"
                       "Ketik 'YES' untuk melanjutkan: ")
        if confirm != "YES":
            print("Dibatalkan.")
            sys.exit(0)

    asyncio.run(archive_old_invoices(args.months, dry_run=args.dry_run))