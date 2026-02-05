from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload, aliased
import pytz
from datetime import date, datetime, time
from typing import List, Optional

# Impor model, skema, dan dependensi yang relevan
from ..schemas.report import RevenueReportResponse, InvoiceReportItem
from ..models.invoice import Invoice as InvoiceModel
from ..models.invoice_archive import InvoiceArchive as InvoiceArchiveModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel
from ..database import get_db
from ..auth import get_current_active_user  # Sesuaikan path jika berbeda
from ..models.harga_layanan import HargaLayanan as HargaLayananMode

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    responses={404: {"description": "Not found"}},
)


@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    start_date: date,
    end_date: date,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    today_date = date.today()

    # --- 1. FINANCIAL SUMMARY (CASH FLOW) ---
    # Berdasarkan Pembayaran yang DITERIMA dalam periode ini (paid_at)
    # Filter: paid_at between start and end
    
    payment_filter = [
        InvoiceModel.status_invoice == "Lunas",
        InvoiceModel.paid_at.between(start_datetime, end_datetime),
    ]
    if alamat:
        payment_filter.append(PelangganModel.alamat == alamat)
    if id_brand:
        payment_filter.append(PelangganModel.id_brand == id_brand)
        
    payment_query = (
        select(InvoiceModel)
        .join(InvoiceModel.pelanggan)
        .where(and_(*payment_filter))
    )
    # Execute for Active Invoices
    paid_invoices_active = (await db.execute(payment_query)).scalars().all()

    # Archive Invoices (Payments)
    archive_payment_filter = [
        InvoiceArchiveModel.status_invoice == "Lunas",
        InvoiceArchiveModel.paid_at.between(start_datetime, end_datetime),
    ]
    # Note: Pelanggan filter applies same way
    if alamat:
        archive_payment_filter.append(PelangganModel.alamat == alamat)
    if id_brand:
        archive_payment_filter.append(PelangganModel.id_brand == id_brand)

    archive_payment_query = (
        select(InvoiceArchiveModel)
        .join(InvoiceArchiveModel.pelanggan)
        .where(and_(*archive_payment_filter))
    )
    paid_invoices_archive = (await db.execute(archive_payment_query)).scalars().all()

    all_paid_invoices = list(paid_invoices_active) + list(paid_invoices_archive)

    total_pemasukan = sum(inv.total_harga or 0 for inv in all_paid_invoices)
    
    # Financial Summary Object
    financial_summary = {
        "total_pemasukan": total_pemasukan,
        "total_pengeluaran": 0.0, # Placeholder, belum ada modul expense
        "saldo_akhir": total_pemasukan # - pengeluaran
    }

    # --- 2. BILLING SUMMARY & TAX & PAYMENT METHODS ---
    # Berdasarkan Tagihan yang DICETAK/DIBUAT dalam periode ini (tgl_invoice atau tgl_jatuh_tempo?)
    # Biasanya laporan tagihan bulanan melihat tgl_jatuh_tempo di bulan tersebut.
    # Kita gunakan tgl_jatuh_tempo karena lebih mencerminkan "Tagihan Bulan X".
    
    billing_filter = [
        InvoiceModel.tgl_jatuh_tempo.between(start_date, end_date)
    ]
    if alamat:
        billing_filter.append(PelangganModel.alamat == alamat)
    if id_brand:
        billing_filter.append(PelangganModel.id_brand == id_brand)
    
    # Eager load harga_layanan untuk perhitungan pajak
    billing_query = (
        select(InvoiceModel)
        .join(InvoiceModel.pelanggan)
        .options(selectinload(InvoiceModel.pelanggan).selectinload(PelangganModel.harga_layanan))
        .where(and_(*billing_filter))
    )
    billed_invoices_active = (await db.execute(billing_query)).scalars().all()

    # Archive Billing
    billing_filter_archive = [
        InvoiceArchiveModel.tgl_jatuh_tempo.between(start_date, end_date)
    ]
    if alamat:
        billing_filter_archive.append(PelangganModel.alamat == alamat)
    if id_brand:
        billing_filter_archive.append(PelangganModel.id_brand == id_brand)
    
    billing_query_archive = (
        select(InvoiceArchiveModel)
        .join(InvoiceArchiveModel.pelanggan)
        .options(selectinload(InvoiceArchiveModel.pelanggan).selectinload(PelangganModel.harga_layanan))
        .where(and_(*billing_filter_archive))
    )
    billed_invoices_archive = (await db.execute(billing_query_archive)).scalars().all()

    all_billed_invoices = list(billed_invoices_active) + list(billed_invoices_archive)
    
    # Initialize Aggregators
    bill_stats = {
        "total_tagihan": {"count": 0, "nominal": 0.0, "diskon": 0.0, "biaya_pasang": 0.0, "total": 0.0},
        "lunas": {"count": 0, "nominal": 0.0, "diskon": 0.0, "biaya_pasang": 0.0, "total": 0.0},
        "pending": {"count": 0, "nominal": 0.0, "diskon": 0.0, "biaya_pasang": 0.0, "total": 0.0},
        "telat": {"count": 0, "nominal": 0.0, "diskon": 0.0, "biaya_pasang": 0.0, "total": 0.0},
    }
    
    tax_stats = {
        "total": {"ppn": 0.0, "bhp": 0.0, "uso": 0.0, "total_pajak": 0.0},
        "lunas": {"ppn": 0.0, "bhp": 0.0, "uso": 0.0, "total_pajak": 0.0},
        "pending": {"ppn": 0.0, "bhp": 0.0, "uso": 0.0, "total_pajak": 0.0},
        "telat": {"ppn": 0.0, "bhp": 0.0, "uso": 0.0, "total_pajak": 0.0},
    }
    
    payment_methods_map = {} # key: method name, val: {count, amount, pajak, diskon}

    for inv in all_billed_invoices:
        # Determine Category
        category = "pending"
        # Logika Status:
        # 1. Lunas -> "lunas"
        # 2. Belum Dibayar AND tgl_jatuh_tempo < today -> "telat"
        # 3. Belum Dibayar AND tgl_jatuh_tempo >= today -> "pending"
        # 4. Expired/Kadaluarsa -> "telat"
        
        status = inv.status_invoice
        
        # Safe Date Conversion for comparison
        inv_due_date = inv.tgl_jatuh_tempo
        if isinstance(inv_due_date, datetime):
            inv_due_date = inv_due_date.date()
            
        if status == "Lunas":
            category = "lunas"
        elif status in ["Kadaluarsa", "Expired", "Suspend", "Suspended"]:
            category = "telat"
        elif status == "Belum Dibayar":
            if inv_due_date < today_date:
                category = "telat"
            else:
                category = "pending"
        else:
            category = "pending" # Default fallback

        # Extract Values
        qty = 1
        total_final = float(inv.total_harga or 0)
        diskon = float(inv.diskon_amount or 0)
        biaya_pasang = 0.0 # Belum ada kolom biaya pasang explicit, asumsikan 0 atau ambil dari item lain nanti
        
        # Calculate Tax (Reverse Engineering or Fetch from Brand)
        # Formula: Total Final = (Harga Dasar * (1 + TaxRate)) - Diskon
        # Jadi: Harga Dasar * (1 + TaxRate) = Total Final + Diskon
        # Harga Dasar = (Total Final + Diskon) / (1 + TaxRate)
        # Pajak = (Total Final + Diskon) - Harga Dasar
        
        tax_rate = 0.11 # Default 11%
        if inv.pelanggan and inv.pelanggan.harga_layanan and inv.pelanggan.harga_layanan.pajak:
            tax_rate = float(inv.pelanggan.harga_layanan.pajak) / 100.0
            
        gross_amount = total_final + diskon
        base_price = gross_amount / (1 + tax_rate)
        pajak_amt = gross_amount - base_price
        
        nominal_gross = base_price # Nominal usually means pre-tax, pre-discount price OR gross bill?
        # Di reference image: Nominal 83jt, Total 83jt (mirip). Diskon kecil.
        # Let's use Gross Amount (inc tax, exc diskon) as "Nominal"? 
        # Or Base Price? 
        # Biasanya "Tagihan" = Subtotal. "Total" = Grand Total.
        # Kita pakai Base Price sebagai "Nominal" (Harga Layanan murni).
        
        # Update Bill Stats (Category)
        bill_stats[category]["count"] += qty
        bill_stats[category]["nominal"] += base_price
        bill_stats[category]["diskon"] += diskon
        bill_stats[category]["biaya_pasang"] += biaya_pasang
        bill_stats[category]["total"] += total_final
        
        # Update Bill Stats (Total)
        bill_stats["total_tagihan"]["count"] += qty
        bill_stats["total_tagihan"]["nominal"] += base_price
        bill_stats["total_tagihan"]["diskon"] += diskon
        bill_stats["total_tagihan"]["biaya_pasang"] += biaya_pasang
        bill_stats["total_tagihan"]["total"] += total_final
        
        # Update Tax Stats
        # Asumsi semua PPN, BHP/USO 0 dulu
        tax_stats[category]["ppn"] += pajak_amt
        tax_stats[category]["total_pajak"] += pajak_amt
        
        tax_stats["total"]["ppn"] += pajak_amt
        tax_stats["total"]["total_pajak"] += pajak_amt

        # Payment Method Stats
        # Logic: 
        # 1. If method is explicitly set -> Use it
        # 2. If no method and Status is "Belum Dibayar" -> "Belum Dibayar"
        # 3. If no method and Status is "Lunas" -> "Manual / Tunai" (Assumption for older/manual data)
        # 4. Others -> Group by Status
        
        raw_method = inv.metode_pembayaran
        
        if raw_method:
            method = raw_method
        else:
            if inv.status_invoice == "Belum Dibayar":
                 method = "Belum Dibayar"
            elif inv.status_invoice == "Lunas":
                 method = "Manual / Tunai"
            else:
                 method = f"Status: {inv.status_invoice}"

        # Clean key name
        method = method.strip().title() 
        
        if method not in payment_methods_map:
            payment_methods_map[method] = {"count": 0, "amount": 0.0, "pajak": 0.0, "diskon": 0.0}
        
        payment_methods_map[method]["count"] += 1
        payment_methods_map[method]["amount"] += total_final
        payment_methods_map[method]["pajak"] += pajak_amt
        payment_methods_map[method]["diskon"] += diskon

    # Convert Payment Methods Map to List
    payment_methods_list = [
        {
            "method": k, 
            "count": v["count"], 
            "total_amount": v["amount"],
            "pajak": v["pajak"],
            "diskon": v["diskon"]
        } 
        for k, v in payment_methods_map.items()
    ]
    # Sort by amount desc
    payment_methods_list.sort(key=lambda x: x["total_amount"], reverse=True)

    return RevenueReportResponse(
        total_pendapatan=financial_summary["total_pemasukan"], # Legacy
        total_invoices=bill_stats["total_tagihan"]["count"], # Legacy
        financial_summary=financial_summary,
        billing_summary=bill_stats,
        tax_summary=tax_stats,
        payment_methods=payment_methods_list,
        rincian_invoice=[],  # Selalu kembalikan list kosong, detail via endpoint terpisah
    )


@router.get("/revenue/details", response_model=List[InvoiceReportItem])
async def get_revenue_report_details(
    start_date: date,
    end_date: date,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Endpoint baru yang HANYA mengambil rincian invoice dengan paginasi.
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)

    # --- KONDISI FILTER UMUM (SAMA SEPERTI DI ATAS) ---
    filter_conditions = [
        InvoiceModel.status_invoice == "Lunas",
        InvoiceModel.paid_at.between(start_datetime, end_datetime),
    ]
    if alamat:
        filter_conditions.append(PelangganModel.alamat == alamat)
    if id_brand:
        filter_conditions.append(PelangganModel.id_brand == id_brand)

    # --- QUERY UNTUK RINCIAN INVOICE (DENGAN PAGINASI) ---
    
    # 1. Query Active Invoices (Tanpa limit/offset dulu)
    active_query = (
        select(
            InvoiceModel.id,
            InvoiceModel.invoice_number,
            InvoiceModel.total_harga,
            InvoiceModel.paid_at,
            InvoiceModel.metode_pembayaran,
            InvoiceModel.tgl_jatuh_tempo,
            InvoiceModel.pelanggan_id,
            InvoiceModel.is_reinvoice,
            PelangganModel.nama,
            PelangganModel.alamat,
            PelangganModel.id_brand,
        )
        .join(InvoiceModel.pelanggan)
        .where(and_(*filter_conditions))
    )

    # 2. Query Archive Invoices
    archive_filter_conditions = [
        InvoiceArchiveModel.status_invoice == "Lunas",
        InvoiceArchiveModel.paid_at.between(start_datetime, end_datetime),
    ]
    if alamat:
        archive_filter_conditions.append(PelangganModel.alamat == alamat)
    if id_brand:
        archive_filter_conditions.append(PelangganModel.id_brand == id_brand)

    archive_query = (
        select(
            InvoiceArchiveModel.id,
            InvoiceArchiveModel.invoice_number,
            InvoiceArchiveModel.total_harga,
            InvoiceArchiveModel.paid_at,
            InvoiceArchiveModel.metode_pembayaran,
            InvoiceArchiveModel.tgl_jatuh_tempo,
            InvoiceArchiveModel.pelanggan_id,
            InvoiceArchiveModel.is_reinvoice,
            PelangganModel.nama,
            PelangganModel.alamat,
            PelangganModel.id_brand,
        )
        .join(InvoiceArchiveModel.pelanggan)
        .where(and_(*archive_filter_conditions))
    )

    # Execute both queries
    active_result = await db.execute(active_query)
    archive_result = await db.execute(archive_query)
    
    active_data = active_result.fetchall()
    archive_data = archive_result.fetchall()

    # 3. Combine and Sort
    all_data = active_data + archive_data
    # Sort by paid_at desc
    all_data.sort(key=lambda x: x.paid_at if x.paid_at else datetime.min, reverse=True)

    # 4. Apply Pagination
    if limit is not None:
        start_idx = skip
        end_idx = skip + limit
        invoice_pelanggan_data = all_data[start_idx:end_idx]
    else:
        invoice_pelanggan_data = all_data

    rincian_invoice_list = []
    wib_timezone = pytz.timezone("Asia/Jakarta")

    # Ambil semua id_brand unik untuk query harga_layanan
    id_brands = [data.id_brand for data in invoice_pelanggan_data if data.id_brand]

    # Query harga_layanan terkait
    brand_harga_layanan = {}
    if id_brands:
        harga_layanan_query = select(HargaLayananMode).where(HargaLayananMode.id_brand.in_(id_brands))
        harga_layanan_result = await db.execute(harga_layanan_query)
        for harga_layanan in harga_layanan_result.scalars().all():
            brand_harga_layanan[harga_layanan.id_brand] = harga_layanan

    for data in invoice_pelanggan_data:
        # Tentukan tipe invoice berdasarkan tanggal jatuh tempo dan is_reinvoice
        invoice_type = "Otomatis"
        if data.tgl_jatuh_tempo and data.tgl_jatuh_tempo.day > 1:
            invoice_type = "Prorate"

        # Tentukan metode pembayaran final berdasarkan is_reinvoice
        metode_pembayaran_final = data.metode_pembayaran
        if data.is_reinvoice:
            # Jika reinvoice, tambahkan suffix " - Reinvoice"
            if not metode_pembayaran_final:
                metode_pembayaran_final = f"Xendit - {invoice_type} - Reinvoice"
            else:
                # Jika sudah ada nilai, tambahkan " - Reinvoice" jika belum ada
                if "Reinvoice" not in metode_pembayaran_final:
                    metode_pembayaran_final = f"{metode_pembayaran_final} - Reinvoice"
        else:
            # Pasang baru / invoice biasa
            if not metode_pembayaran_final:
                metode_pembayaran_final = f"Xendit - {invoice_type}"

        paid_at_wib = None
        if data.paid_at:
            # Pastikan paid_at adalah timezone-aware (UTC)
            utc_time = data.paid_at.replace(tzinfo=pytz.utc)
            # Konversi ke WIB
            paid_at_wib = utc_time.astimezone(wib_timezone)

        # Get harga_layanan berdasarkan id_brand
        harga_layanan = brand_harga_layanan.get(data.id_brand)

        # Buat item laporan
        report_item = InvoiceReportItem(
            invoice_number=data.invoice_number,
            pelanggan_nama=data.nama if data.nama else "N/A",
            paid_at=paid_at_wib,
            total_harga=data.total_harga,
            metode_pembayaran=metode_pembayaran_final,  # Gunakan nilai yang sudah diproses
            alamat=data.alamat if data.alamat else "N/A",
            id_brand=harga_layanan.brand if harga_layanan else "N/A",
        )
        rincian_invoice_list.append(report_item)

    # Kembalikan hanya list rinciannya
    return rincian_invoice_list
