# app/services/telegram_ai_monitor.py
"""
🤖 Telegram AI Log Monitor Service
====================================
Service untuk monitoring log billing system menggunakan Qwen AI (Alibaba Cloud)
dan mengirimkan laporan analisis ke Bot Telegram.

Features:
- Membaca log dari file (app.log, errors.log, access.log)
- Mengambil data billing langsung dari database (real-time)
- Menganalisis log menggunakan Qwen AI (Alibaba DashScope)
- Mengirimkan hasil analisis ke Telegram Bot
- Scheduled monitoring (cron job)
- Error detection & alerting

Config:
- ALIBABA_CLOUD_API_KEY: API key untuk Qwen AI
- TELEGRAM_BOT_TOKEN: Token bot Telegram
- TELEGRAM_CHAT_ID: Chat ID tujuan laporan
"""

import os
import re
import logging
import traceback
import httpx
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, case, and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Invoice as InvoiceModel
from ..models import Langganan as LanggananModel
from ..models import Pelanggan as PelangganModel

logger = logging.getLogger("app.services.telegram_ai_monitor")

# ====================================================================
# KONFIGURASI
# ====================================================================

# Alibaba Cloud Qwen AI
ALIBABA_API_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
ALIBABA_API_KEY = os.getenv("ALIBABA_CLOUD_API_KEY", "")
QWEN_MODEL = "qwen-plus"

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8194252122:AAFEfRqzIv3BM4LKk8q_bw70QnTWhXH18Yc")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1127703225")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Log file paths (Prioritaskan .env, lalu relative path, baru default Linux)
LOG_PATHS = {
    "app_log": os.getenv("LOG_PATH_APP", "logs/app.log"),
    "error_log": os.getenv("LOG_PATH_ERROR", "logs/errors.log"),
    "access_log": os.getenv("LOG_PATH_ACCESS", "logs/access.log"),
}

# Jika path relative tidak ada, dan bukan di Windows, coba common Linux path
if not os.path.exists(LOG_PATHS["app_log"]) and os.name != "nt":
    LINUX_FALLBACK = "/root/billing/logs/"
    if os.path.exists(os.path.join(LINUX_FALLBACK, "app.log")):
        LOG_PATHS = {
            "app_log": os.path.join(LINUX_FALLBACK, "app.log"),
            "error_log": os.path.join(LINUX_FALLBACK, "errors.log"),
            "access_log": os.path.join(LINUX_FALLBACK, "access.log"),
        }


# ====================================================================
# LOG READER - Membaca log files
# ====================================================================

def read_latest_logs(log_type: str = "app_log", n_lines: int = 100) -> str:
    """Membaca N baris terakhir dari file log."""
    log_path = LOG_PATHS.get(log_type, LOG_PATHS["app_log"])
    
    if not os.path.exists(log_path):
        logger.warning(f"File log tidak ditemukan: {log_path}")
        return f"[File log tidak ditemukan: {log_path}]"
    
    try:
        # PENTING: Cek ukuran file, jika 0 berikan warning
        if os.path.getsize(log_path) == 0:
            return f"[File log ditemukan tapi KOSONG: {log_path}. Pastikan aplikasi sudah menulis log.]"

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            if not lines:
                return f"[File log KOSONG: {log_path}]"
            # Ambil N baris terakhir
            recent_lines = lines[-n_lines:]
            return "".join(recent_lines)
    except Exception as e:
        logger.error(f"Gagal membaca log {log_path}: {e}")
        return f"[Error membaca log {log_path}: {e}]"


def extract_scheduler_logs(raw_log: str) -> str:
    """Ekstrak hanya log yang relevan dengan scheduler/jobs."""
    relevant_keywords = [
        "JOBS", "APSCHEDUL", "job_generate_invoices", "job_suspend_services",
        "job_verify_payments", "job_retry_mikrotik_syncs", "job_retry_failed_invoices",
        "SCHEDULER", "Invoice", "invoice", "BERHASIL", "GAGAL", "FAIL", "ERROR",
        "WARNING", "CRITICAL", "Suspend", "suspend", "✅", "❌", "⚠️", "🟢",
        "payment", "Payment", "Xendit", "Mikrotik", "mikrotik", "ROLLBACK"
    ]
    
    filtered_lines = []
    # Remove ANSI color codes
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    
    for line in raw_log.split("\n"):
        clean_line = ansi_escape.sub("", line).strip()
        if any(keyword in clean_line for keyword in relevant_keywords):
            filtered_lines.append(clean_line)
    
    return "\n".join(filtered_lines[-80:])  # Max 80 baris relevan


def extract_error_logs(raw_log: str) -> str:
    """Ekstrak hanya log yang mengandung error/warning."""
    error_keywords = ["ERROR", "FAIL", "CRITICAL", "WARNING", "❌", "⚠️", "Exception", "Traceback"]
    
    filtered_lines = []
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    
    for line in raw_log.split("\n"):
        clean_line = ansi_escape.sub("", line).strip()
        if any(keyword in clean_line for keyword in error_keywords):
            filtered_lines.append(clean_line)
    
    return "\n".join(filtered_lines[-30:])  # Max 30 baris error


# ====================================================================
# DATABASE READER - Mengambil data real-time dari database
# ====================================================================

async def get_billing_summary() -> dict:
    """
    Mengambil ringkasan billing dari database secara real-time.
    Data ini akan dikirim ke AI sebagai konteks tambahan.
    """
    summary = {
        "tanggal": date.today().strftime("%d %B %Y"),
        "total_pelanggan_aktif": 0,
        "total_invoice_bulan_ini": 0,
        "invoice_lunas": 0,
        "invoice_belum_bayar": 0,
        "invoice_kadaluarsa": 0,
        "invoice_gagal_xendit": 0,
        "total_revenue_bulan_ini": 0,
        "user_jatuh_tempo_hari_ini": 0,
        "user_jatuh_tempo_5_hari": 0,
        "user_suspended": 0,
        "daftar_user_belum_bayar": [],
        "daftar_user_gagal_invoice": [],
    }
    
    try:
        async with AsyncSessionLocal() as db:
            today = date.today()
            start_of_month = today.replace(day=1)
            
            # Total pelanggan aktif
            active_count = await db.execute(
                select(func.count(LanggananModel.id)).where(
                    LanggananModel.status == "Aktif"
                )
            )
            summary["total_pelanggan_aktif"] = active_count.scalar() or 0
            
            # Total pelanggan suspended
            suspended_count = await db.execute(
                select(func.count(LanggananModel.id)).where(
                    LanggananModel.status == "Suspended"
                )
            )
            summary["user_suspended"] = suspended_count.scalar() or 0
            
            # Invoice bulan ini - breakdown per status
            invoice_stats = await db.execute(
                select(
                    InvoiceModel.status_invoice,
                    func.count(InvoiceModel.id).label("jumlah"),
                    func.coalesce(func.sum(InvoiceModel.total_harga), 0).label("total")
                )
                .where(InvoiceModel.tgl_invoice >= start_of_month)
                .group_by(InvoiceModel.status_invoice)
            )
            
            for row in invoice_stats.all():
                status, jumlah, total = row
                summary["total_invoice_bulan_ini"] += jumlah
                if status == "Lunas":
                    summary["invoice_lunas"] = jumlah
                    summary["total_revenue_bulan_ini"] = float(total)
                elif status in ("Belum Dibayar", "Expired"):
                    summary["invoice_belum_bayar"] += jumlah
                elif status == "Kadaluarsa":
                    summary["invoice_kadaluarsa"] = jumlah
            
            # Invoice yang gagal generate payment link (xendit_id NULL)
            failed_xendit = await db.execute(
                select(func.count(InvoiceModel.id)).where(
                    InvoiceModel.tgl_invoice >= start_of_month,
                    InvoiceModel.xendit_id.is_(None),
                    InvoiceModel.status_invoice == "Belum Dibayar"
                )
            )
            summary["invoice_gagal_xendit"] = failed_xendit.scalar() or 0
            
            # User yang jatuh tempo hari ini
            due_today = await db.execute(
                select(func.count(LanggananModel.id)).where(
                    LanggananModel.tgl_jatuh_tempo == today,
                    LanggananModel.status == "Aktif"
                )
            )
            summary["user_jatuh_tempo_hari_ini"] = due_today.scalar() or 0
            
            # User yang jatuh tempo dalam 5 hari ke depan (candidate invoice)
            target_date = today + timedelta(days=5)
            due_5_days = await db.execute(
                select(func.count(LanggananModel.id)).where(
                    LanggananModel.tgl_jatuh_tempo >= today,
                    LanggananModel.tgl_jatuh_tempo <= target_date,
                    LanggananModel.status == "Aktif"
                )
            )
            summary["user_jatuh_tempo_5_hari"] = due_5_days.scalar() or 0
            
            # Daftar user yang belum bayar (max 20 nama)
            from sqlalchemy.orm import selectinload
            unpaid_invoices = await db.execute(
                select(InvoiceModel)
                .options(selectinload(InvoiceModel.pelanggan))
                .where(
                    InvoiceModel.tgl_invoice >= start_of_month,
                    InvoiceModel.status_invoice.in_(["Belum Dibayar", "Expired"])
                )
                .limit(20)
            )
            for inv in unpaid_invoices.scalars().all():
                if inv.pelanggan:
                    summary["daftar_user_belum_bayar"].append({
                        "nama": inv.pelanggan.nama,
                        "invoice": inv.invoice_number,
                        "total": float(inv.total_harga),
                        "jatuh_tempo": str(inv.tgl_jatuh_tempo)
                    })
            
            # Daftar user yang gagal invoice (xendit error)
            failed_invoices = await db.execute(
                select(InvoiceModel)
                .options(selectinload(InvoiceModel.pelanggan))
                .where(
                    InvoiceModel.tgl_invoice >= start_of_month,
                    InvoiceModel.xendit_id.is_(None),
                    InvoiceModel.status_invoice == "Belum Dibayar"
                )
                .limit(10)
            )
            for inv in failed_invoices.scalars().all():
                if inv.pelanggan:
                    summary["daftar_user_gagal_invoice"].append({
                        "nama": inv.pelanggan.nama,
                        "invoice": inv.invoice_number,
                        "error": getattr(inv, 'xendit_error_message', 'Unknown')
                    })
    
    except Exception as e:
        logger.error(f"Error getting billing summary: {e}")
        summary["error"] = str(e)
    
    return summary


# ====================================================================
# SYSTEM METRICS - Untuk Ubuntu Server (CPU, RAM, Disk)
# ====================================================================

import shutil
import psutil # Library untuk cek RAM/CPU

def get_system_metrics() -> dict:
    """Mengambil stats hardware server (Ubuntu/Linux)."""
    metrics = {
        "os": os.name,
        "cpu_usage": 0,
        "ram_usage": 0,
        "disk_usage": 0,
        "uptime": "N/A"
    }
    
    try:
        # CPU Usage
        metrics["cpu_usage"] = psutil.cpu_percent(interval=1)
        
        # RAM Usage
        ram = psutil.virtual_memory()
        metrics["ram_usage"] = ram.percent
        
        # Disk Usage (Root partition)
        disk = shutil.disk_usage("/")
        metrics["disk_usage"] = round((disk.used / disk.total) * 100, 2)
        
        # Uptime (Linux only)
        if os.name != "nt":
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_days = int(uptime_seconds // 86400)
                uptime_hours = int((uptime_seconds % 86400) // 3600)
                metrics["uptime"] = f"{uptime_days} hari, {uptime_hours} jam"
        else:
            # Simple uptime placeholder for Windows
            metrics["uptime"] = "Running on Windows"
            
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        
    return metrics


# ====================================================================
# QWEN AI ANALYZER - Analisis log menggunakan AI
# ====================================================================

async def analyze_with_qwen(log_data: str, billing_summary: dict, report_type: str = "daily") -> str:
    """
    Mengirim data log, billing summary, dan system metrics ke Qwen AI.
    """
    if not ALIBABA_API_KEY:
        return "⚠️ ALIBABA_CLOUD_API_KEY belum dikonfigurasi. Silakan set di .env file."
    
    # Ambil HW metrics
    hw_metrics = get_system_metrics()
    
    # System prompt berdasarkan tipe laporan
    system_prompts = {
        "daily": (
            "Anda adalah asisten billing PortalFTTHv2 yang bertugas membuat laporan harian. "
            "Anda menganalisis log server, data billing, dan kesehatan hardware (Ubuntu/Linux). "
            "PENTING: Gunakan bahasa Indonesia yang profesional dan ringkas. "
            "Format output menggunakan emoji untuk visual yang bagus di Telegram. "
            "Jangan sertakan informasi sensitive seperti API key."
        ),
        "invoice": "Anda fokus pada analisis invoice...", # Disingkat untuk efisiensi replacement
        "error": "Anda fokus pada analisis error log...",
        "server": "Anda fokus pada kesehatan server dan hardware...",
    }
    
    # Build prompt dengan data
    system_text = (
        f"🖥️ INFO SERVER (Ubuntu):\n"
        f"- CPU Usage: {hw_metrics['cpu_usage']}%\n"
        f"- RAM Usage: {hw_metrics['ram_usage']}%\n"
        f"- Disk Usage: {hw_metrics['disk_usage']}%\n"
        f"- Uptime: {hw_metrics['uptime']}\n\n"
    )

    billing_text = "\n".join([
        f"📅 Tanggal: {billing_summary.get('tanggal', 'N/A')}",
        f"👥 Total Pelanggan Aktif: {billing_summary.get('total_pelanggan_aktif', 0)}",
        f"🔒 User Suspended: {billing_summary.get('user_suspended', 0)}",
        f"📄 Total Invoice Bulan Ini: {billing_summary.get('total_invoice_bulan_ini', 0)}",
        f"✅ Invoice Lunas: {billing_summary.get('invoice_lunas', 0)}",
        f"⏳ Invoice Belum Bayar: {billing_summary.get('invoice_belum_bayar', 0)}",
        f"⚠️ Invoice Gagal Xendit: {billing_summary.get('invoice_gagal_xendit', 0)}",
        f"💰 Revenue Bulan Ini: Rp {billing_summary.get('total_revenue_bulan_ini', 0):,.0f}",
    ])
    
    # Daftar user - sample
    unpaid_text = ""
    unpaid_list = billing_summary.get("daftar_user_belum_bayar", [])
    if unpaid_list:
        unpaid_text = "\n\nUser Belum Bayar (sample):\n" + "\n".join([f"- {u['nama']} ({u['jatuh_tempo']})" for u in unpaid_list[:5]])

    # Prompt content
    prompt_content = (
        f"{system_text}"
        f"=== DATA BILLING SYSTEM ===\n{billing_text}{unpaid_text}\n\n"
        f"=== LOG SERVER (Terbaru) ===\n{log_data[:3500]}\n\n"
        "=== TUGAS ANDA ===\n"
        "Berdasarkan data di atas, buatlah laporan ringkas mencakup:\n"
        "1. 📊 Status Billing Hari Ini\n"
        "2. 🖥️ Kondisi Hardware Server (CPU/RAM/Disk - berikan peringatan jika >80%)\n"
        "3. ✅ Ringkasan Invoice Berhasil vs Gagal\n"
        "4. ⚠️ Analisis Masalah dari Log & Saran Solusi\n"
        "   (CATATAN: Jika log kosong atau error, berikan instruksi kepada admin untuk mengecek path log di .env dan menjalankan scripts/check_production_logs.sh)\n"
        "5. 🏥 Kesimpulan Kesehatan Sistem (Healthy/Warning/Critical)\n\n"
        "FORMAT: Gunakan emoji, maksimal 3500 karakter."
    )
    
    headers = {
        "Authorization": f"Bearer {ALIBABA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompts.get(report_type, system_prompts["daily"])},
            {"role": "user", "content": prompt_content}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(ALIBABA_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            logger.info(f"Qwen AI analysis completed. Tokens used: {result.get('usage', {})}")
            return ai_response
            
    except httpx.TimeoutException:
        error_msg = "⚠️ Timeout saat menghubungi Qwen AI. Coba lagi nanti."
        logger.error(error_msg)
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"⚠️ Qwen AI API error: {e.response.status_code} - {e.response.text[:200]}"
        logger.error(error_msg)
        return error_msg
    except KeyError as e:
        error_msg = f"⚠️ Response format error dari Qwen AI: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"⚠️ Error saat analisis AI: {str(e)}"
        logger.error(error_msg)
        return error_msg


# ====================================================================
# TELEGRAM SENDER - Mengirim pesan ke Telegram
# ====================================================================

async def send_telegram_message(
    text: str, 
    chat_id: str = None, 
    parse_mode: str = "Markdown",
    disable_notification: bool = False
) -> bool:
    """
    Mengirim pesan ke Telegram Bot.
    Otomatis split pesan jika melebihi 4096 karakter.
    """
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.warning("TELEGRAM_BOT_TOKEN belum dikonfigurasi!")
        return False
    
    url = f"{TELEGRAM_API_URL}/sendMessage"
    
    # Split pesan jika terlalu panjang (Telegram limit: 4096 chars)
    max_length = 4000
    messages = []
    
    if len(text) <= max_length:
        messages.append(text)
    else:
        # Split by paragraphs
        parts = text.split("\n\n")
        current_msg = ""
        for part in parts:
            if len(current_msg) + len(part) + 2 > max_length:
                if current_msg:
                    messages.append(current_msg)
                current_msg = part
            else:
                current_msg = current_msg + "\n\n" + part if current_msg else part
        if current_msg:
            messages.append(current_msg)
    
    success = True
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, msg in enumerate(messages):
                payload = {
                    "chat_id": target_chat_id,
                    "text": msg,
                    "parse_mode": parse_mode,
                    "disable_notification": disable_notification,
                }
                
                response = await client.post(url, json=payload)
                
                if response.status_code != 200:
                    # Retry tanpa parse_mode jika Markdown error
                    logger.warning(f"Telegram send failed with Markdown, retrying without parse_mode...")
                    payload["parse_mode"] = ""
                    response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Telegram message {i+1}/{len(messages)} sent successfully")
                else:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    success = False
                    
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        success = False
    
    return success


# ====================================================================
# TELEGRAM INTERACTIVE HANDLER (Webhook)
# ====================================================================

async def handle_telegram_webhook(update: dict) -> None:
    """
    Menangani pesan masuk dari user di Telegram.
    """
    message = update.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").lower()
    user_name = message.get("from", {}).get("first_name", "Admin")

    # 1. Security Check: Hanya balas jika dari Chat ID yang terdaftar
    if chat_id != TELEGRAM_CHAT_ID:
        logger.warning(f"📩 Pesan diabaikan dari Chat ID tidak dikenal: {chat_id}")
        return

    logger.info(f"📩 Pesan diterima dari {user_name}: {text}")

    # 2. Logic Balasan Berdasarkan Keyword
    try:
        if any(k in text for k in ["status", "kondisi", "cek server", "sehat"]):
            # Trigger laporan health check
            await send_telegram_message(f"⏳ Sedang mengecek kondisi server untuk Anda, {user_name}...")
            await run_server_health_check()
            
        elif any(k in text for k in ["laporan", "billing", "tagihan", "summary"]):
            # Trigger laporan billing harian
            await send_telegram_message(f"⏳ Menyiapkan ringkasan billing terbaru...")
            await run_daily_report()
            
        elif any(k in text for k in ["error", "masalah", "cek log"]):
            # Trigger cek error
            await send_telegram_message(f"🔍 Memeriksa log server untuk mencari error...")
            await run_error_alert()
            
        else:
            # Jika user bertanya hal umum, biarkan AI menjawab secara bebas
            await send_telegram_message(f"🤔 Menanyakan ke Qwen AI: '{text}'...")
            
            # Ambil data singkat untuk konteks AI
            summary = await get_billing_summary()
            hw = get_system_metrics()
            
            prompt = (
                f"User {user_name} bertanya: '{text}'\n\n"
                f"Konteks Server:\n- CPU: {hw['cpu_usage']}%, RAM: {hw['ram_usage']}%, Uptime: {hw['uptime']}\n"
                f"Konteks Billing:\n- Pelanggan Aktif: {summary['total_pelanggan_aktif']}\n"
                f"- Revenue: Rp {summary['total_revenue_bulan_ini']:,.0f}\n\n"
                "Jawablah pertanyaan user tersebut secara singkat, ceria, dan profesional sebagai asisten IT."
            )
            
            ai_response = await analyze_with_qwen(text, summary, "daily") # Re-use analyzer
            await send_telegram_message(ai_response)

    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {e}")
        await send_telegram_message(f"❌ Maaf {user_name}, terjadi kesalahan saat memproses permintaan Anda.")


async def run_daily_report() -> None:
    """
    Membuat dan mengirim laporan harian ke Telegram.
    Dipanggil oleh scheduler setiap hari (misal jam 08:00 dan 20:00).
    """
    logger.info("🤖 Starting daily billing report generation...")

    
    try:
        # 1. Ambil log terbaru
        app_log = read_latest_logs("app_log", n_lines=200)
        scheduler_logs = extract_scheduler_logs(app_log)
        
        # 2. Ambil data billing dari database
        billing_summary = await get_billing_summary()
        
        # 3. Analisis dengan Qwen AI
        ai_analysis = await analyze_with_qwen(scheduler_logs, billing_summary, "daily")
        
        # 4. Build final message
        header = (
            "📊 *LAPORAN BILLING PORTALFTTHV2*\n"
            f"📅 {datetime.now().strftime('%d %B %Y - %H:%M WIB')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        footer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 _Dianalisis oleh Qwen AI (Alibaba Cloud)_\n"
            "📡 _Billing System: billingftth.my.id_"
        )
        
        full_message = header + ai_analysis + footer
        
        # 5. Kirim ke Telegram
        sent = await send_telegram_message(full_message)
        
        if sent:
            logger.info("✅ Daily report sent to Telegram successfully")
        else:
            logger.error("❌ Failed to send daily report to Telegram")
            
    except Exception as e:
        error_msg = f"❌ Error generating daily report: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Kirim error notification ke Telegram
        await send_telegram_message(
            f"🚨 *ERROR LAPORAN BILLING*\n\n{error_msg}\n\nSilakan cek server logs.",
            disable_notification=False
        )


async def run_error_alert() -> None:
    """
    Mengecek error log dan mengirim alert jika ada error kritis.
    Dipanggil setiap 30 menit atau 1 jam.
    """
    logger.info("🔍 Checking for critical errors...")
    
    try:
        # Baca error log
        error_log = read_latest_logs("error_log", n_lines=50)
        error_lines = extract_error_logs(error_log)
        
        # Juga cek app log untuk error
        app_log = read_latest_logs("app_log", n_lines=100)
        app_errors = extract_error_logs(app_log)
        
        combined_errors = f"{error_lines}\n{app_errors}".strip()
        
        if not combined_errors:
            logger.info("✅ No critical errors found")
            return
        
        # Cek apakah ada error CRITICAL
        has_critical = "CRITICAL" in combined_errors or "VERY CRITICAL" in combined_errors
        
        if has_critical:
            # Ambil data billing untuk konteks
            billing_summary = await get_billing_summary()
            
            # Analisis error dengan AI
            ai_analysis = await analyze_with_qwen(combined_errors, billing_summary, "error")
            
            alert_msg = (
                "🚨 *ALERT: ERROR TERDETEKSI!*\n"
                f"📅 {datetime.now().strftime('%d %B %Y - %H:%M WIB')}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{ai_analysis}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 _Auto-detected by Billing Monitor_"
            )
            
            await send_telegram_message(alert_msg, disable_notification=False)
            logger.warning("⚠️ Critical error alert sent to Telegram")
        
    except Exception as e:
        logger.error(f"Error in error alert check: {e}")


async def run_invoice_report() -> None:
    """
    Laporan fokus pada status invoice.
    Dipanggil setelah job_generate_invoices selesai.
    """
    logger.info("📄 Generating invoice status report...")
    
    try:
        billing_summary = await get_billing_summary()
        
        # Baca log terkait invoice generation
        app_log = read_latest_logs("app_log", n_lines=150)
        invoice_logs = extract_scheduler_logs(app_log)
        
        ai_analysis = await analyze_with_qwen(invoice_logs, billing_summary, "invoice")
        
        message = (
            "📄 *LAPORAN STATUS INVOICE*\n"
            f"📅 {datetime.now().strftime('%d %B %Y - %H:%M WIB')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{ai_analysis}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 _Dianalisis oleh Qwen AI_"
        )
        
        await send_telegram_message(message)
        logger.info("✅ Invoice report sent to Telegram")
        
    except Exception as e:
        logger.error(f"Error generating invoice report: {e}")


async def run_server_health_check() -> None:
    """
    Cek kesehatan server dan kirim status ke Telegram.
    Bisa dipanggil 2x sehari (pagi & malam).
    """
    logger.info("🏥 Running server health check...")
    
    try:
        billing_summary = await get_billing_summary()
        app_log = read_latest_logs("app_log", n_lines=100)
        
        # Cek scheduler status
        scheduler_logs = extract_scheduler_logs(app_log)
        
        ai_analysis = await analyze_with_qwen(scheduler_logs, billing_summary, "server")
        
        message = (
            "🏥 *SERVER HEALTH CHECK*\n"
            f"📅 {datetime.now().strftime('%d %B %Y - %H:%M WIB')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{ai_analysis}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 _Server Monitor - Qwen AI_"
        )
        
        await send_telegram_message(message)
        logger.info("✅ Server health report sent to Telegram")
        
    except Exception as e:
        logger.error(f"Error in server health check: {e}")


# ====================================================================
# TEST CONNECTION
# ====================================================================

async def test_connection() -> dict:
    """
    Test koneksi ke Qwen AI dan Telegram.
    Bisa dipanggil via API endpoint untuk verifikasi setup.
    """
    result = {
        "qwen_ai": {"status": "pending", "message": ""},
        "telegram": {"status": "pending", "message": ""},
        "database": {"status": "pending", "message": ""},
        "log_files": {"status": "pending", "message": ""},
    }
    
    # Test 1: Qwen AI
    try:
        if not ALIBABA_API_KEY:
            result["qwen_ai"] = {"status": "error", "message": "API key not configured"}
        else:
            headers = {
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": QWEN_MODEL,
                "messages": [{"role": "user", "content": "Sapa admin PortalFTTHv2 dalam 1 kalimat ceria."}],
                "max_tokens": 100,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(ALIBABA_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                ai_msg = resp.json()["choices"][0]["message"]["content"]
                result["qwen_ai"] = {"status": "ok", "message": ai_msg}
    except Exception as e:
        result["qwen_ai"] = {"status": "error", "message": str(e)}
    
    # Test 2: Telegram
    try:
        sent = await send_telegram_message(
            f"✅ *Test Koneksi Berhasil!*\n\n"
            f"🤖 AI Says: {result['qwen_ai'].get('message', 'N/A')}\n\n"
            f"📅 {datetime.now().strftime('%d %B %Y %H:%M:%S WIB')}\n"
            f"📡 Server: billingftth.my.id"
        )
        result["telegram"] = {"status": "ok" if sent else "error", "message": "Message sent" if sent else "Failed"}
    except Exception as e:
        result["telegram"] = {"status": "error", "message": str(e)}
    
    # Test 3: Database
    try:
        summary = await get_billing_summary()
        result["database"] = {
            "status": "ok",
            "message": f"Active: {summary['total_pelanggan_aktif']} users"
        }
    except Exception as e:
        result["database"] = {"status": "error", "message": str(e)}
    
    # Test 4: Log files
    log_status = []
    for name, path in LOG_PATHS.items():
        exists = os.path.exists(path)
        log_status.append(f"{name}: {'✅' if exists else '❌'} ({path})")
    result["log_files"] = {"status": "ok", "message": "\n".join(log_status)}
    
    return result
