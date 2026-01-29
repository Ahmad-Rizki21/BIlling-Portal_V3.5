"""
Email Service untuk kirim notifikasi terkait layanan FTTH.
Menggunakan SMTP server dari mail.jelantik.com
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service untuk mengirim email notifikasi menggunakan SMTP.
    Hanya digunakan untuk brand JELANTIK (ajn-02) dan JELANTIK NAGRAK (ajn-03).
    """

    # Brand codes yang boleh menggunakan mail.jelantik.com
    ALLOWED_BRANDS = ["ajn-02", "ajn-03"]  # JELANTIK dan JELANTIK NAGRAK

    @staticmethod
    def is_brand_allowed(id_brand: str) -> bool:
        """
        Cek apakah brand diperbolehkan menggunakan email service.
        Hanya JELANTIK (ajn-02) dan JELANTIK NAGRAK (ajn-03) yang boleh.
        """
        return id_brand in EmailService.ALLOWED_BRANDS

    @staticmethod
    async def send_suspend_notification(
        db: AsyncSession,
        pelanggan_email: str,
        pelanggan_nama: str,
        total_tagihan: int,
        id_brand: str,
        langganan_id: int,
        tgl_jatuh_tempo: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Kirim notifikasi email saat layanan di-suspend karena telat bayar.

        Args:
            db: Database session
            pelanggan_email: Email pelanggan
            pelanggan_nama: Nama pelanggan
            id_brand: Brand code (ajn-02, ajn-03)
            langganan_id: ID langganan
            tgl_jatuh_tempo: Tanggal jatuh tempo pembayaran

        Returns:
            Dict dengan status success/failed dan pesan
        """
        # Cek apakah brand diperbolehkan
        if not EmailService.is_brand_allowed(id_brand):
            logger.warning(f"Brand {id_brand} tidak diperbolehkan menggunakan email service. Skipping email notification.")
            return {
                "success": False,
                "message": f"Brand {id_brand} tidak diperbolehkan menggunakan email service",
                "status": "skipped"
            }

        # Cek apakah email tersedia
        if not pelanggan_email:
            logger.warning(f"Tidak ada email untuk pelanggan {pelanggan_nama}. Skipping email notification.")
            return {
                "success": False,
                "message": "Email pelanggan tidak tersedia",
                "status": "skipped"
            }

        # Cek konfigurasi SMTP
        smtp_host = getattr(settings, "SMTP_HOST", None)
        smtp_port = getattr(settings, "SMTP_PORT", None)
        smtp_username = getattr(settings, "SMTP_USERNAME", None)
        smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        smtp_from = getattr(settings, "SMTP_FROM_EMAIL", "noreply@jelantik.com")

        if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
            logger.error("Konfigurasi SMTP belum lengkap. Silakan setting di .env file.")
            return {
                "success": False,
                "message": "Konfigurasi SMTP belum lengkap",
                "status": "failed"
            }

        try:
            # Buat email message dengan mixed untuk bisa attach file
            msg = MIMEMultipart("mixed")
            msg["Subject"] = f"⚠️ Layanan Internet Anda Ditangguhkan (Suspended)"
            msg["From"] = f"Jelantik FTTH <{smtp_from}>"
            msg["To"] = pelanggan_email

            # Format tanggal jatuh tempo
            tgl_tempo_str = tgl_jatuh_tempo.strftime("%d %B %Y") if tgl_jatuh_tempo else "N/A"

            # Format total tagihan ke Rupiah
            def format_rupiah(amount):
                if amount is None:
                    return "Rp 0"
                return f"Rp {amount:,.0f}".replace(",", ".")

            total_tagihan_formatted = format_rupiah(total_tagihan)

            # HTML Email Template - Clean & Minimalist (Bubble Style)
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Layanan Ditangguhkan - Jelantik FTTH</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 40px auto;
                        background: white;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    .logo-section {{
                        text-align: center;
                        padding: 40px 40px 30px 40px;
                        background: white;
                    }}
                    .logo-section img {{
                        width: 120px;
                        height: auto;
                    }}
                    .brand-line {{
                        height: 4px;
                        background: linear-gradient(90deg, #0066cc 0%, #00a8ff 100%);
                        margin: 0;
                    }}
                    .content {{
                        padding: 40px 50px;
                        background: white;
                    }}
                    .greeting {{
                        font-size: 15px;
                        color: #333;
                        margin-bottom: 20px;
                    }}
                    .message {{
                        font-size: 15px;
                        color: #555;
                        line-height: 1.7;
                        margin-bottom: 25px;
                    }}
                    .message strong {{
                        color: #d32f2f;
                    }}
                    .info-box {{
                        background: #f8f9fa;
                        border-left: 3px solid #0066cc;
                        padding: 20px;
                        margin: 25px 0;
                        border-radius: 4px;
                    }}
                    .info-box h3 {{
                        margin: 0 0 15px 0;
                        font-size: 14px;
                        color: #0066cc;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }}
                    .info-row {{
                        padding: 12px 0;
                        border-bottom: 1px solid #e9ecef;
                    }}
                    .info-row:last-child {{
                        border-bottom: none;
                    }}
                    .info-label {{
                        color: #666;
                        font-size: 13px;
                        margin-bottom: 5px;
                        display: block;
                    }}
                    .info-value {{
                        color: #333;
                        font-weight: 600;
                        font-size: 15px;
                        display: block;
                    }}
                    .amount {{
                        color: #0066cc;
                        font-size: 16px;
                        font-weight: 700;
                    }}
                    .status-badge {{
                        background: #d32f2f;
                        color: white;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }}
                    .steps {{
                        margin: 25px 0;
                    }}
                    .steps p {{
                        font-size: 15px;
                        color: #333;
                        margin-bottom: 12px;
                        font-weight: 500;
                    }}
                    .steps ol {{
                        margin: 0;
                        padding-left: 20px;
                    }}
                    .steps li {{
                        font-size: 14px;
                        color: #555;
                        padding: 6px 0;
                        line-height: 1.6;
                    }}
                    .contact-section {{
                        background: #f0f7ff;
                        padding: 20px;
                        border-radius: 6px;
                        margin: 25px 0;
                    }}
                    .contact-section p {{
                        margin: 0 0 12px 0;
                        font-size: 14px;
                        color: #333;
                    }}
                    .contact-section a {{
                        color: #0066cc;
                        text-decoration: none;
                        font-weight: 500;
                    }}
                    .contact-section a:hover {{
                        text-decoration: underline;
                    }}
                    .closing {{
                        font-size: 14px;
                        color: #555;
                        margin: 25px 0;
                    }}
                    .signature {{
                        font-size: 14px;
                        color: #333;
                        margin-top: 20px;
                    }}
                    .divider {{
                        height: 1px;
                        background: #e9ecef;
                        margin: 30px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 30px 40px;
                        background: #fafafa;
                        border-top: 1px solid #e9ecef;
                    }}
                    .footer p {{
                        margin: 5px 0;
                        font-size: 12px;
                        color: #999;
                        line-height: 1.5;
                    }}
                    .footer a {{
                        color: #0066cc;
                        text-decoration: none;
                    }}
                    .social-links {{
                        margin: 20px 0 15px 0;
                    }}
                    .social-links a {{
                        display: inline-block;
                        width: 32px;
                        height: 32px;
                        margin: 0 5px;
                        background: #e9ecef;
                        border-radius: 50%;
                        text-align: center;
                        line-height: 32px;
                        color: #666;
                        text-decoration: none;
                        font-size: 14px;
                    }}
                    .social-links a:hover {{
                        background: #0066cc;
                        color: white;
                    }}
                    @media only screen and (max-width: 600px) {{
                        .email-container {{
                            margin: 20px 10px;
                        }}
                        .content {{
                            padding: 30px 25px;
                        }}
                        .logo-section {{
                            padding: 30px 25px 20px 25px;
                        }}
                        .info-row {{
                            flex-direction: column;
                        }}
                        .info-value {{
                            margin-top: 5px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <!-- Logo Section -->
                    <div class="logo-section">
                        <div style="font-size: 28px; font-weight: 700; color: #0066cc; letter-spacing: -0.5px;">
                            Jelantik FTTH
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px; letter-spacing: 0.5px;">
                            FIBER TO THE HOME INTERNET SERVICE
                        </div>
                    </div>
                    
                    <!-- Brand Line -->
                    <div class="brand-line"></div>
                    
                    <!-- Content -->
                    <div class="content">
                        <div class="greeting">
                            Hello,
                        </div>
                        
                        <div class="message">
                            Kami informasikan bahwa layanan internet Anda telah <strong>ditangguhkan (suspended)</strong> dikarenakan pembayaran belum diterima sampai dengan tanggal jatuh tempo.
                        </div>
                        
                        <!-- Invoice Details -->
                        <div class="info-box">
                            <h3>Detail Tagihan</h3>
                            <div class="info-row">
                                <span class="info-label">Nama Pelanggan</span>
                                <span class="info-value"> {pelanggan_nama}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Tanggal Jatuh Tempo</span>
                                <span class="info-value"> {tgl_tempo_str}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Total Tagihan</span>
                                <span class="info-value amount"> {total_tagihan_formatted}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Status Layanan</span>
                                <span class="info-value"><span class="status-badge">Suspended</span></span>
                            </div>
                        </div>
                        
                        <!-- Steps -->
                        <div class="steps">
                            <p>Untuk mengaktifkan kembali layanan internet Anda:</p>
                            <ol>
                                <li>Lakukan pembayaran tagihan yang belum lunas</li>
                                <li>Konfirmasi pembayaran ke tim kami melalui WhatsApp atau Email</li>
                                <li>Layanan akan aktif kembali dalam waktu 1-24 jam setelah pembayaran dikonfirmasi</li>
                            </ol>
                        </div>
                        
                        <!-- Contact -->
                        <div class="contact-section">
                            <p>Jika Anda sudah melakukan pembayaran atau memiliki pertanyaan, silakan hubungi kami:</p>
                            <p>📱 WhatsApp: <a href="https://wa.me/6282223616884">+62 822-2361-6884</a></p>
                            <p>📧 Email: <a href="mailto:support@jelantik.com">support@jelantik.com</a></p>
                        </div>
                        
                        <div class="closing">
                            Terima kasih atas perhatian dan kerjasamanya.
                        </div>
                        
                        <div class="signature">
                            <strong>Tim Jelantik FTTH</strong>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div class="footer">
                        <div class="social-links">
                            <a href="https://wa.me/6282223616884" title="WhatsApp">💬</a>
                            <a href="mailto:support@jelantik.com" title="Email">📧</a>
                            <a href="https://jelantik.com" title="Website">🌐</a>
                        </div>
                        <p>Email ini dikirim otomatis oleh sistem Billing Jelantik FTTH</p>
                        <p>Tanggal: {datetime.now().strftime("%d %B %Y, %H:%M WIB")}</p>
                        <p style="margin-top: 15px; color: #666;">© 2025 Jelantik FTTH. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Text version untuk fallback
            text_body = f"""
            Yth. {pelanggan_nama},

            Layanan internet Anda telah DITANGGUHKAN (SUSPENDED) dikarenakan pembayaran belum diterima.

            Tanggal Jatuh Tempo: {tgl_tempo_str}
            Status: Suspended

            Untuk mengaktifkan kembali layanan, silakan lakukan pembayaran dan konfirmasi ke tim kami.

            Terima kasih,
            Tim JELANTIK FTTH
            """

            # Attach both versions
            # Create alternative part for text and HTML
            alt_msg = MIMEMultipart("alternative")
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            alt_msg.attach(part1)
            alt_msg.attach(part2)
            msg.attach(alt_msg)

            # Generate dan attach PDF suspend notification
            try:
                from .pdf_service import PDFInvoiceService

                pdf_bytes = await PDFInvoiceService.generate_suspend_pdf(db, langganan_id)

                if pdf_bytes:
                    # Attach PDF
                    pdf_attachment = MIMEBase("application", "pdf")
                    pdf_attachment.set_payload(pdf_bytes)
                    encoders.encode_base64(pdf_attachment)

                    # Filename dengan timestamp
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        f"attachment; filename=Notifikasi_Suspend_{pelanggan_nama.replace(' ', '_')}_{timestamp_str}.pdf"
                    )
                    msg.attach(pdf_attachment)
                    logger.info(f"✅ PDF suspend berhasil di-attach untuk langganan ID {langganan_id}")
                else:
                    logger.warning(f"⚠️ Gagal generate PDF untuk langganan ID {langganan_id}. Email dikirim tanpa attachment.")

            except Exception as pdf_error:
                logger.warning(f"⚠️ Error generate PDF: {pdf_error}. Email dikirim tanpa attachment.")

            # Kirim email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email suspend berhasil dikirim ke {pelanggan_email} untuk langganan ID {langganan_id}")

            return {
                "success": True,
                "message": "Email berhasil dikirim",
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }

        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ SMTP Authentication Error. Cek username/password SMTP.")
            return {
                "success": False,
                "message": "SMTP Authentication Error",
                "status": "failed"
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP Error: {e}")
            return {
                "success": False,
                "message": f"SMTP Error: {str(e)}",
                "status": "failed"
            }
        except Exception as e:
            logger.error(f"❌ Error mengirim email: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "status": "failed"
            }

    @staticmethod
    async def send_payment_reminder(
        db: AsyncSession,
        pelanggan_email: str,
        pelanggan_nama: str,
        id_brand: str,
        nomor_invoice: str,
        total_tagihan: float,
        tgl_jatuh_tempo: datetime,
    ) -> Dict[str, Any]:
        """
        Kirim notifikasi email reminder pembayaran.

        Args:
            db: Database session
            pelanggan_email: Email pelanggan
            pelanggan_nama: Nama pelanggan
            id_brand: Brand code
            nomor_invoice: Nomor invoice
            total_tagihan: Total tagihan
            tgl_jatuh_tempo: Tanggal jatuh tempo

        Returns:
            Dict dengan status success/failed
        """
        # Cek apakah brand diperbolehkan
        if not EmailService.is_brand_allowed(id_brand):
            return {
                "success": False,
                "message": f"Brand {id_brand} tidak diperbolehkan menggunakan email service",
                "status": "skipped"
            }

        if not pelanggan_email:
            return {
                "success": False,
                "message": "Email pelanggan tidak tersedia",
                "status": "skipped"
            }

        # Implementation similar to send_suspend_notification
        # TODO: Implement payment reminder email template
        return {
            "success": False,
            "message": "Payment reminder email not yet implemented",
            "status": "pending"
        }
