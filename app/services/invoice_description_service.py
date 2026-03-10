# app/services/invoice_description_service.py
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ..utils.date_utils import safe_format_date, safe_to_datetime

logger = logging.getLogger("app.services.invoice_description")

def get_invoice_description(langganan, paket, invoice, brand) -> str:
    """
    Logika penentuan deskripsi invoice untuk Xendit.
    Ported dari original logic di routers/invoice.py
    """
    if langganan.metode_pembayaran == "Prorate":
        harga_normal_full = float(paket.harga) * (1 + (float(brand.pajak or 0) / 100))
        invoice_date = safe_to_datetime(invoice.tgl_invoice)
        due_date = safe_to_datetime(invoice.tgl_jatuh_tempo)

        # Invoice pertama: tgl_invoice tidak pada tanggal 1
        is_first_invoice = invoice_date.day != 1

        if is_first_invoice:
            periode_start = invoice_date
            if due_date.day == 1:
                periode_end = due_date - timedelta(days=1)
            else:
                periode_end = due_date
        else:
            if due_date.day == 1:
                periode_end = due_date - timedelta(days=1)
                periode_start = periode_end.replace(day=1)
            else:
                periode_start = due_date.replace(day=1)
                periode_end = due_date

        # Tagihan gabungan (Combined)
        if float(invoice.total_harga or 0) > (harga_normal_full + 1):
            periode_prorate_end = invoice_date.replace(day=1) + relativedelta(months=1, days=-1)
            periode_prorate_str = safe_format_date(periode_prorate_end, "%B %Y")
            periode_berikutnya_start = periode_prorate_end + timedelta(days=1)
            periode_berikutnya_end = periode_berikutnya_start + relativedelta(months=1, days=-1)

            return (
                f"Biaya internet up to {paket.kecepatan} Mbps. "
                f"Periode {invoice_date.day}-{periode_prorate_end.day} {periode_prorate_str} + "
                f"Periode {safe_format_date(periode_berikutnya_end, '%B %Y')}"
            )
        else:
            # Prorate Biasa
            if periode_start.month == periode_end.month and periode_start.year == periode_end.year:
                period_desc = f"Periode Tgl {periode_start.day}-{periode_end.day} {safe_format_date(periode_end, '%B %Y')}"
            elif periode_start.year == periode_end.year:
                period_desc = f"Periode Tgl {periode_start.day} {safe_format_date(periode_start, '%B')} - {periode_end.day} {safe_format_date(periode_end, '%B %Y')}"
            else:
                period_desc = f"Periode Tgl {safe_format_date(periode_start, '%d %B %Y')} - {safe_format_date(periode_end, '%d %B %Y')}"

            return f"Biaya internet up to {paket.kecepatan} Mbps, {period_desc}"

    # Default / Otomatis (Monthly)
    jatuh_tempo_str = safe_format_date(invoice.tgl_jatuh_tempo, "%d/%m/%Y")
    return f"Biaya internet up to {paket.kecepatan} Mbps jatuh tempo {jatuh_tempo_str}"
