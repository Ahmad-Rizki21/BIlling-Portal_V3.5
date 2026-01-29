"""
PDF Invoice Service untuk generate invoice PDF
Menggunakan ReportLab untuk generate PDF invoice profesional
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel

logger = logging.getLogger(__name__)


class PDFInvoiceService:
    """
    Service untuk generate PDF invoice dengan branding Jelantik FTTH
    """

    # Konfigurasi warna Jelantik
    COLOR_PRIMARY = colors.HexColor('#0066cc')
    COLOR_SECONDARY = colors.HexColor('#00a8ff')
    COLOR_DARK = colors.HexColor('#1a1a1a')
    COLOR_GRAY = colors.HexColor('#666666')
    COLOR_LIGHT_GRAY = colors.HexColor('#f5f5f5')
    COLOR_SUCCESS = colors.HexColor('#4caf50')
    COLOR_WARNING = colors.HexColor('#ff9800')
    COLOR_DANGER = colors.HexColor('#f44336')

    @staticmethod
    async def generate_invoice_pdf(
        db: AsyncSession,
        invoice_id: int
    ) -> Optional[bytes]:
        """
        Generate PDF untuk invoice tertentu.

        Args:
            db: Database session
            invoice_id: ID invoice yang akan di-generate PDF-nya

        Returns:
            PDF bytes atau None jika gagal
        """
        try:
            # Ambil data invoice dengan relasi
            query = (
                select(InvoiceModel)
                .where(InvoiceModel.id == invoice_id)
            )
            result = await db.execute(query)
            invoice = result.scalar_one_or_none()

            if not invoice:
                logger.error(f"Invoice ID {invoice_id} tidak ditemukan")
                return None

            # Ambil data pelanggan
            query_pelanggan = (
                select(PelangganModel)
                .where(PelangganModel.id == invoice.pelanggan_id)
            )
            result_pelanggan = await db.execute(query_pelanggan)
            pelanggan = result_pelanggan.scalar_one_or_none()

            if not pelanggan:
                logger.error(f"Pelanggan ID {invoice.pelanggan_id} tidak ditemukan")
                return None

            # Generate PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # Build content
            story = []
            story.extend(PDFInvoiceService._build_invoice_content(invoice, pelanggan))

            # Generate PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            logger.info(f"✅ PDF Invoice berhasil di-generate untuk Invoice ID {invoice_id}")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Error generate PDF invoice: {e}")
            return None

    @staticmethod
    def _build_invoice_content(invoice: InvoiceModel, pelanggan: PelangganModel) -> list:
        """
        Build content untuk PDF invoice.
        """
        styles = getSampleStyleSheet()
        content = []

        # Tambahkan custom styles
        styles.add(ParagraphStyle(
            name='JelantikTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=PDFInvoiceService.COLOR_PRIMARY,
            spaceAfter=0.3*cm,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='JelantikSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=PDFInvoiceService.COLOR_GRAY,
            alignment=TA_CENTER,
            letterSpacing=1,
            spaceAfter=1*cm
        ))

        styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=PDFInvoiceService.COLOR_DARK,
            spaceAfter=0.5*cm,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='LabelStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PDFInvoiceService.COLOR_GRAY,
            fontName='Helvetica'
        ))

        styles.add(ParagraphStyle(
            name='ValueStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PDFInvoiceService.COLOR_DARK,
            fontName='Helvetica-Bold'
        ))

        # HEADER - Logo & Brand
        content.append(Paragraph("JELANTIK FTTH", styles['JelantikTitle']))
        content.append(Paragraph("FIBER TO THE HOME INTERNET SERVICE", styles['JelantikSubtitle']))

        # Invoice Title & Info
        invoice_info_data = [
            [
                Paragraph("INVOICE", styles['InvoiceTitle']),
                Paragraph(f"Nomor: {invoice.nomor_invoice or 'N/A'}", styles['ValueStyle']),
                Paragraph(f"Tanggal: {invoice.tgl_invoice.strftime('%d %B %Y') if invoice.tgl_invoice else 'N/A'}", styles['ValueStyle']),
                Paragraph(f"Jatuh Tempo: {invoice.tgl_jatuh_tempo.strftime('%d %B %Y') if invoice.tgl_jatuh_tempo else 'N/A'}", styles['ValueStyle']),
            ]
        ]

        # Status badge
        status_colors = {
            'Lunas': PDFInvoiceService.COLOR_SUCCESS,
            'Belum Dibayar': PDFInvoiceService.COLOR_WARNING,
            'Kadaluarsa': PDFInvoiceService.COLOR_DANGER,
        }
        status_color = status_colors.get(invoice.status_invoice, PDFInvoiceService.COLOR_GRAY)

        # Customer Information
        content.append(Spacer(1, 1*cm))
        content.append(Paragraph("Tagihan Kepada:", styles['LabelStyle']))

        customer_data = [
            ["Nama", ":", Paragraph(pelanggan.nama, styles['ValueStyle'])],
            ["Alamat", ":", Paragraph(pelanggan.alamat or '-', styles['ValueStyle'])],
            ["No. Telepon", ":", Paragraph(pelanggan.no_telp or '-', styles['ValueStyle'])],
            ["Email", ":", Paragraph(pelanggan.email or '-', styles['ValueStyle'])],
        ]

        customer_table = Table(customer_data, colWidths=[4*cm, 0.5*cm, 10*cm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), PDFInvoiceService.COLOR_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(customer_table)

        # Invoice Details Table
        content.append(Spacer(1, 1*cm))
        content.append(Paragraph("Rincian Tagihan:", styles['LabelStyle']))

        invoice_items_data = [
            ["Deskripsi", "Jumlah"],
        ]

        # Add invoice items
        invoice_items_data.append([
            "Pembayaran Internet FTTH",
            f"Rp {invoice.total_harga:,.0f}".replace(",", ".") if invoice.total_harga else "Rp 0"
        ])

        # Add pajak if exists
        if hasattr(invoice, 'pajak') and invoice.pajak:
            invoice_items_data.append([
                f"Pajak ({invoice.pajak}%)",
                "Termasuk"
            ])

        # Add diskon if exists
        if hasattr(invoice, 'diskon_amount') and invoice.diskon_amount:
            invoice_items_data.append([
                f"Diskon",
                f"-Rp {invoice.diskon_amount:,.0f}".replace(",", ".")
            ])

        invoice_table = Table(invoice_items_data, colWidths=[12*cm, 4*cm])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFInvoiceService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, PDFInvoiceService.COLOR_LIGHT_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFInvoiceService.COLOR_LIGHT_GRAY]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(invoice_table)

        # Total Section
        content.append(Spacer(1, 0.5*cm))

        total_data = [
            ["TOTAL TAGIHAN", f"Rp {invoice.total_harga:,.0f}".replace(",", ".") if invoice.total_harga else "Rp 0"],
        ]

        total_table = Table(total_data, colWidths=[12*cm, 4*cm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFInvoiceService.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        content.append(total_table)

        # Payment Info
        content.append(Spacer(1, 1.5*cm))
        content.append(Paragraph("Informasi Pembayaran:", styles['LabelStyle']))

        payment_info = [
            ["Bank Transfer", "BCA"],
            ["No. Rekening", "123-456-7890"],
            ["Atas Nama", "JELANTIK FTTH"],
            ["", ""],
            ["E-Wallet", ["GoPay, OVO, Dana, ShopeePay"]],
            ["", ""],
            ["Keterangan", f"Sertakan nomor invoice: {invoice.nomor_invoice or 'N/A'}"],
        ]

        payment_table = Table(payment_info, colWidths=[4*cm, 10*cm])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), PDFInvoiceService.COLOR_PRIMARY),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(payment_table)

        # Footer
        content.append(Spacer(1, 2*cm))
        content.append(Paragraph(
            "Terima kasih atas kepercayaan Anda menggunakan layanan Jelantik FTTH.",
            styles['LabelStyle']
        ))

        footer_text = f"""
        <para align=center fontSize=9 textColor=#999999>
        JELANTIK FTTH • Fiber To The Home Internet Service<br/>
        Email: support@jelantik.com • WhatsApp: +62 822-2361-6884<br/>
        Invoice ini diterbitkan secara otomatis pada {datetime.now().strftime('%d %B %Y, %H:%M')}
        </para>
        """
        content.append(Paragraph(footer_text, styles['Normal']))

        return content

    @staticmethod
    async def generate_suspend_pdf(
        db: AsyncSession,
        langganan_id: int
    ) -> Optional[bytes]:
        """
        Generate PDF notifikasi suspend dengan style Invoice Professional (1 Halaman + Watermark).
        """
        try:
            from sqlalchemy.orm import joinedload
            
            # Ambil data langganan + paket layanan
            query = (
                select(LanggananModel)
                .options(joinedload(LanggananModel.paket_layanan))
                .where(LanggananModel.id == langganan_id)
                .execution_options(populate_existing=True)
            )
            result = await db.execute(query)
            langganan = result.unique().scalar_one_or_none()

            if not langganan:
                return None

            # Ambil data pelanggan
            query_pelanggan = select(PelangganModel).where(PelangganModel.id == langganan.pelanggan_id)
            result_pelanggan = await db.execute(query_pelanggan)
            pelanggan = result_pelanggan.scalar_one_or_none()

            if not pelanggan:
                return None

            # Setup PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=1.5*cm,
                bottomMargin=1.5*cm
            )

            # --- Watermark Function ---
            def draw_watermark(canvas, doc):
                canvas.saveState()
                
                # Koordinat pojok kanan atas (sejajar dengan header kanan)
                page_width, page_height = A4
                
                # Posisi di atas alamat kanan
                x_pos = page_width - 1.5*cm - 60 # Margin kanan - setengah lebar box
                y_pos = page_height - 1.5*cm + 10 # Sedikit di atas text baris pertama
                
                text = "BELUM LUNAS"
                color = colors.HexColor('#d32f2f') # Merah lebih soft sedikit
                
                # Transparansi
                canvas.setFillAlpha(1) 
                
                # Draw Banner Lurus
                canvas.translate(x_pos, y_pos)
                
                # Banner Rectangle rounded
                path = canvas.beginPath()
                # Kotak ukuran 120x24
                path.roundRect(-60, 0, 120, 24, 4) # width, height, radius
                canvas.setFillColor(color)
                canvas.setStrokeColor(color)
                canvas.drawPath(path, fill=1, stroke=0)
                
                # Text
                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica-Bold", 11)
                canvas.drawCentredString(0, 8, text) # Center vertical alignment approximate
                
                canvas.restoreState()

            # Build content
            story = []
            
            # Spacer awal dikurangi karena watermark sudah rapi
            story.append(Spacer(1, 0.5*cm))
            story.extend(PDFInvoiceService._build_suspend_content(langganan, pelanggan))

            # Build PDF dengan Watermark
            doc.build(story, onFirstPage=draw_watermark, onLaterPages=draw_watermark)

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            logger.info(f"✅ PDF Suspend berhasil di-generate untuk Langganan ID {langganan_id}")
            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Error generate PDF suspend: {e}")
            return None

    @staticmethod
    def _build_suspend_content(langganan: LanggananModel, pelanggan: PelangganModel) -> list:
        """
        Build content Layout Invoice Professional (Compact 1 Halaman).
        """
        styles = getSampleStyleSheet()
        content = []

        # -- Styles Setup --
        style_header_company = ParagraphStyle(
            name='HeaderCompany',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT
        )
        
        style_address_right = ParagraphStyle(
            name='AddressRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_RIGHT,
            leading=12
        )

        style_invoice_strip = ParagraphStyle(
            name='InvoiceStripLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.black,
        )

        style_invoice_strip_small = ParagraphStyle(
            name='InvoiceStripSmall',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#444444'),
            leading=12
        )

        # 1. HEADER SECTION (Logo Kiri - Alamat Kanan)
        # Nama Perusahaan
        logo_text = Paragraph("JELANTIK FTTH", style_header_company)
        
        # Alamat Perusahaan (Kanan) - Tidak perlu padding extra lagi
        company_address = [
            "<b>PT Artacomindo Jejaring Nusa</b>",
            "Grand Prima Bintara, Jl. Terusan I Gusti Ngurah Rai - Bekasi.",
            "Email: support@jelantik.com",
            "WhatsApp: +62 822-2361-6884",
        ]
        address_text = Paragraph("<br/>".join(company_address), style_address_right)

        header_table = Table([[logo_text, address_text]], colWidths=[9*cm, 9*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            # Padding atas kolom kanan ditambahkan sedikit agar tidak nabrak box BELUM LUNAS
            ('TOPPADDING', (1,0), (1,0), 30), 
        ]))
        content.append(header_table)
        content.append(Spacer(1, 1*cm))

        # 2. GRAY STRIP INFO (Invoice #, Tanggal)
        invoice_no = f"INV/SUSPEND/{langganan.id}/{datetime.now().strftime('%m%Y')}"
        today_str = datetime.now().strftime('%d-%m-%Y')
        due_str = langganan.tgl_jatuh_tempo.strftime('%d-%m-%Y') if langganan.tgl_jatuh_tempo else "-"

        strip_data = [
            [
                Paragraph(f"Invoice #{invoice_no}", style_invoice_strip),
            ],
            [
                Paragraph(f"<b>Tanggal Invoice:</b> {today_str}<br/><b>Tanggal Jatuh Tempo:</b> {due_str}", style_invoice_strip_small)
            ]
        ]
        
        strip_table = Table(strip_data, colWidths=[18*cm])
        strip_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')), 
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        content.append(strip_table)
        content.append(Spacer(1, 1*cm))

        # 3. DITAGIHKAN KEPADA
        content.append(Paragraph("<b>Ditagihkan Kepada:</b>", styles['Normal']))
        content.append(Spacer(1, 0.2*cm))
        
        customer_info = f"""
        <b>{pelanggan.nama}</b><br/>
        {pelanggan.alamat or '-'}<br/>
        {pelanggan.no_telp or '-'}<br/>
        {pelanggan.email or '-'}
        """
        content.append(Paragraph(customer_info, styles['Normal']))
        content.append(Spacer(1, 1*cm))

        # 4. TABEL ITEM TAGIHAN (Dengan PPN)
        # Kalkulasi PPN 11%
        total_gross = float(langganan.harga_awal) if langganan.harga_awal else 0
        # Asumsi harga_awal adalah Total yang harus dibayar (sudah termasuk PPN)
        dpp = total_gross / 1.11
        ppn = total_gross - dpp
        
        nama_paket = langganan.paket_layanan.nama_paket if langganan.paket_layanan else "Layanan Internet"

        # Table Header
        table_header = ["Deskripsi", "Total"]
        
        # Rows
        row_paket = [
            Paragraph(nama_paket, styles['Normal']), 
            f"Rp {dpp:,.0f}".replace(",", ".")
        ]
        
        row_ppn = [
            Paragraph("PPN (11%)", styles['Normal']), 
            f"Rp {ppn:,.0f}".replace(",", ".")
        ]
        
        row_total = [
            "Total", 
            f"Rp {total_gross:,.0f}".replace(",", ".")
        ]

        table_data = [
            table_header,
            row_paket,
            row_ppn,
            row_total
        ]

        item_table = Table(table_data, colWidths=[13*cm, 5*cm])
        item_table.setStyle(TableStyle([
            # Header Style
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
            ('PADDING', (0,0), (-1,-1), 10),
            
            # Content Style
            ('ALIGN', (0,1), (0,-1), 'LEFT'),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            
            # Total Row Style (Last Row)
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f8f9fa')),
            ('TOPPADDING', (0,-1), (-1,-1), 12),
        ]))
        content.append(item_table)

        # 5. REMOVED PAYMENT METHOD SECTION (As requested)
        content.append(Spacer(1, 2*cm))

        # Footer Simple
        footer_text = f"""
        <para align=center fontSize=8 textColor=#999999>
        JELANTIK FTTH • Fiber To The Home Internet Service<br/>
        Dokumen ini diterbitkan secara otomatis pada {datetime.now().strftime('%d %B %Y, %H:%M')}<br/>
        </para>
        """
        content.append(Paragraph(footer_text, styles['Normal']))

        return content
