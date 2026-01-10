"""
Contoh fungsi untuk mencari invoice dari tabel utama dan arsip.

Ini menunjukkan cara menggabungkan hasil dari dua tabel terpisah
untuk memberikan hasil pencarian menyeluruh.
"""
from sqlalchemy import select, union_all
from sqlalchemy.orm import Session
from ..models.invoice import Invoice
from ..models.invoice_archive import InvoiceArchive


def search_invoices_from_all_tables(db: Session, search_term: str = None, status: str = None, start_date: str = None, end_date: str = None):
    """
    Mencari invoice dari tabel `invoices` dan `invoices_archive`.

    Args:
        db (Session): Session database SQLAlchemy.
        search_term (str, optional): Kata kunci untuk mencari di invoice_number, nama_pelanggan, dll.
        status (str, optional): Filter berdasarkan status_invoice.
        start_date (str, optional): Filter tanggal awal (format YYYY-MM-DD).
        end_date (str, optional): Filter tanggal akhir (format YYYY-MM-DD).

    Returns:
        List[Invoice]: Gabungan hasil dari kedua tabel.
    """
    # Buat query untuk tabel utama (invoices)
    query_main = select(Invoice)
    if search_term:
        # Contoh filter pencarian dasar
        query_main = query_main.where(Invoice.invoice_number.like(f"%{search_term}%"))
        # Menambahkan filter lain sesuai kebutuhan (misalnya nama pelanggan jika tersedia)

    if status:
        query_main = query_main.where(Invoice.status_invoice == status)

    if start_date:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        query_main = query_main.where(Invoice.tgl_invoice >= start_dt)

    if end_date:
        from datetime import datetime
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        query_main = query_main.where(Invoice.tgl_invoice <= end_dt)


    # Buat query untuk tabel arsip (invoices_archive)
    query_archive = select(InvoiceArchive)
    if search_term:
        query_archive = query_archive.where(InvoiceArchive.invoice_number.like(f"%{search_term}%"))

    if status:
        query_archive = query_archive.where(InvoiceArchive.status_invoice == status)

    if start_date:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        query_archive = query_archive.where(InvoiceArchive.tgl_invoice >= start_dt)

    if end_date:
        from datetime import datetime
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        query_archive = query_archive.where(InvoiceArchive.tgl_invoice <= end_dt)

    # Gabungkan hasil query
    # union_all digunakan karena struktur kolom sama
    combined_query = union_all(query_main, query_archive)

    # Eksekusi dan kembalikan hasil
    # Karena hasilnya bisa berupa Invoice atau InvoiceArchive, kita perlu hati-hati
    # Satu pendekatan adalah mengembalikan hasil mentah atau mengonversinya ke dict
    # Di sini kita asumsikan struktur sama dan gunakan result.scalars().all()
    # Tapi SQLAlchemy mungkin memerlukan pendekatan khusus untuk union hasil objek model.
    # Cara yang lebih aman adalah mengembalikan hasil sebagai dict.
    # Atau gunakan `aliased` dan `with_entities` untuk mengambil kolom spesifik yang identik.

    # Contoh pendekatan aman: ambil semua kolom, eksekusi, dan konversi ke objek/representasi umum
    result_main = db.execute(query_main).scalars().all()
    result_archive = db.execute(query_archive).scalars().all()

    # Gabungkan list hasil
    all_results = result_main + result_archive

    # Urutkan jika perlu (misalnya berdasarkan tanggal invoice secara menurun)
    all_results.sort(key=lambda x: x.tgl_invoice, reverse=True)

    return all_results

# Alternatif: Gunakan raw SQL untuk UNION jika kompleksitas query meningkat
# from sqlalchemy import text
# def search_invoices_raw_sql(db: Session, ...):
#     sql = text("""
#         SELECT * FROM invoices WHERE ... -- kondisi pencarian
#         UNION ALL
#         SELECT * FROM invoices_archive WHERE ... -- kondisi pencarian yang sama
#         ORDER BY ...
#     """)
#     result = db.execute(sql)
#     return result.fetchall()