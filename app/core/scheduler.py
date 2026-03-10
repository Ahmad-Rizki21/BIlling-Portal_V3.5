import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError

# Import jobs
from ..jobs import (
    job_generate_invoices,
    job_retry_failed_invoices,
    job_retry_mikrotik_syncs,
    job_send_payment_reminders,
    job_suspend_services,
    job_verify_payments,
    job_archive_historical_invoices,
)

# Import Telegram jobs
from ..services.telegram_ai_monitor import (
    run_daily_report,
    run_error_alert,
    run_server_health_check,
)

logger = logging.getLogger("app.scheduler")

def setup_scheduler(scheduler: AsyncIOScheduler):
    """
    Mengatur semua tugas harian (scheduler) aplikasi.
    Memisahkan konfigurasi dari main.py untuk kemudahan pemeliharaan.
    """
    
    #==============================================================GENERATE INVOICE====================================================================================#
    # Generate invoice setiap hari jam 10:00 pagi untuk langganan yang jatuh tempo 5 hari lagi (H-5).
    # NOTE: Saat ini dinonaktifkan di kode lama, jika ingin diaktifkan hapus tanda komentar di bawah.
    # scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job", replace_existing=True)
    #==============================================================GENERATE INVOICE====================================================================================#

    #==============================================================SUSPEND SERVICES (ENHANCED WITH ROLLBACK)=======================================================================#
    # Suspend services tepat tanggal 5 jam 00:00 untuk pelanggan yang telat bayar dari jatuh tempo tanggal 1.
    # ENHANCED: Sekarang dengan automatic Mikrotik rollback jika database gagal (ZERO INCONSISTENCY!)
    # scheduler.add_job(
    #     job_suspend_services,
    #     'cron',
    #     day=5,
    #     hour=0,
    #     minute=0,
    #     timezone='Asia/Jakarta',
    #     id="suspend_services_job",
    #     replace_existing=True,
    #     max_instances=1,  # Prevent duplicate runs
    #     misfire_grace_time=300  # 5 minutes grace time for missed runs
    # )
    #==============================================================SUSPEND SERVICES (ENHANCED WITH ROLLBACK)=======================================================================#


    #==============================================================VERIFY PAYMENTS (PAYMENT RECONCILIATION)=======================================================================#
    # Memverifikasi pembayaran yang mungkin terlewat setiap 15 menit.
    # Penting untuk antisipasi webhook callback yang gagal dari Xendit
    # scheduler.add_job(job_verify_payments, 'interval', minutes=15, id="verify_payments_job", replace_existing=True, max_instances=1)
    #==============================================================VERIFY PAYMENTS (PAYMENT RECONCILIATION)=======================================================================#


    #==============================================================MIKROTIK SYNC RETRY=======================================================================#
    # Mencoba ulang sinkronisasi Mikrotik yang gagal setiap 5 menit.
    # Penting untuk user yang suspend/unsuspend gagal di Mikrotik
    # scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job", replace_existing=True, max_instances=1)
    #==============================================================MIKROTIK SYNC RETRY=======================================================================#


    #==============================================================RETRY FAILED INVOICES=======================================================================#
    # Retry invoice yang gagal dibuat payment link setiap 1 jam
    # Penting untuk invoice yang gagal generate payment link ke Xendit
    # scheduler.add_job(job_retry_failed_invoices, 'interval', hours=1, id="retry_failed_invoices_job", replace_existing=True, max_instances=1)
    #==============================================================RETRY FAILED INVOICES=======================================================================#


    #==============================================================COLLECT TRAFFIC DARI MIKROTIK=======================================================================#
    # Setup traffic monitoring jobs
    # from ..jobs_traffic import setup_traffic_monitoring_jobs
    # setup_traffic_monitoring_jobs(scheduler)
    #==============================================================COLLECT TRAFFIC DARI MIKROTIK=======================================================================#


    #==============================================================ARCHIVE INVOICE LAMA=======================================================================#
    # Archive invoice lama setiap 3 bulan sekali (Januari, April, Juli, Oktober)
    # Job ini memindahkan invoice dengan status Lunas/Kadaluarsa/Batal yang lebih dari 12 bulan
    # ke tabel invoices_archive untuk menjaga performa database
    # scheduler.add_job(
    #     job_archive_historical_invoices,
    #     'cron',
    #     month='1,4,7,10',  # Januari, April, Juli, Oktober
    #     day=1,             # Tanggal 1 setiap triwulan
    #     hour=3,            # Jam 03:00 pagi (traffic minimal)
    #     minute=0,
    #     timezone='Asia/Jakarta',
    #     id="archive_invoices_job",
    #     replace_existing=True,
    #     max_instances=1,        # Cegah job duplikat
    #     misfire_grace_time=3600 # 1 jam grace time jika server sempat mati
    # )
    #==============================================================ARCHIVE INVOICE LAMA=======================================================================#

    #==============================================================REMAINDERS INVOICE=======================================================================#
    # Mengirim pengingat pembayaran setiap hari jam 8 pagi.
    # scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job", replace_existing=True)
    #==============================================================REMAINDERS INVOICE=======================================================================#

    #==============================================================TELEGRAM AI MONITOR=======================================================================#
    # 🤖 Laporan harian Billing System ke Telegram via Qwen AI
    # Jalan 2x sehari: pagi jam 08:00 dan malam jam 20:00
    # scheduler.add_job(
    #     run_daily_report,
    #     'cron',
    #     hour='8,20',
    #     minute=0,
    #     timezone='Asia/Jakarta',
    #     id="telegram_daily_report_job",
    #     replace_existing=True,
    #     max_instances=1,
    #     misfire_grace_time=600  # 10 menit grace time
    # )

    # # 🚨 Error Alert - Cek error kritis setiap 1 jam
    # scheduler.add_job(
    #     run_error_alert,
    #     'interval',
    #     hours=1,
    #     id="telegram_error_alert_job",
    #     replace_existing=True,
    #     max_instances=1
    # )

    # # 🏥 Server Health Check - Setiap hari jam 06:00
    # scheduler.add_job(
    #     run_server_health_check,
    #     'cron',
    #     hour=6,
    #     minute=0,
    #     timezone='Asia/Jakarta',
    #     id="telegram_health_check_job",
    #     replace_existing=True,
    #     max_instances=1
    # )
    #==============================================================TELEGRAM AI MONITOR=======================================================================#
    
    # Log scheduler info
    _print_scheduler_status(scheduler)

def _print_scheduler_status(scheduler: AsyncIOScheduler):
    """
    Mencetak status scheduler ke console untuk verifikasi saat startup.
    Memeriksa ketersediaan job ID untuk menentukan apakah status-nya AKTIF atau Dinonaktifkan.
    Ini memperbaiki kebingungan di mana log menyatakan 'AKTIF' padahal kode di-comment.
    """
    
    # helper function to check if job is active
    def is_active(job_id):
        return "✅ AKTIF" if scheduler.get_job(job_id) else "⏭️  Dinonaktifkan"

    print("="*80)
    print("📅 SCHEDULED JOBS STATUS (V5.0 Optimized)")
    print("="*80)
    print(f"{is_active('generate_invoices_job')} Invoice Generation: Setiap hari jam 10:00 WIB (H-5)")
    print(f"{is_active('suspend_services_job')} Suspend Services: Setiap tanggal 5 jam 00:00 WIB")
    print(f"{is_active('send_reminders_job')} Payment Reminders: Notifikasi Pengingat")
    print(f"{is_active('verify_payments_job')} Payment Verification: Setiap 15 menit")
    print(f"{is_active('retry_mikrotik_syncs_job')} Mikrotik Sync Retry: Setiap 5 menit")
    print(f"{is_active('retry_failed_invoices_job')} Payment Link Retry: Setiap 1 jam")
    print(f"{is_active('traffic_collection')} Traffic Monitoring: Real-time collection")
    print(f"{is_active('archive_invoices_job')} Archive Invoice: Data archiving")
    print(f"{is_active('telegram_daily_report_job')} Telegram Daily Report: Laporan Harian")
    print(f"{is_active('telegram_error_alert_job')} Telegram Error Alert: Monitoring Error")
    print(f"{is_active('telegram_health_check_job')} Telegram Health Check: Status Server")
    print("="*80)

def start_scheduler(scheduler: AsyncIOScheduler):
    """Membuka scheduler dengan safety check."""
    try:
        scheduler.start()
        print("🚀 Scheduler telah dimulai!")
        logger.info("✅ Scheduler started successfully")
    except SchedulerAlreadyRunningError:
        print("⚠️  Scheduler sudah berjalan, melanjutkan dengan instance yang ada...")
        logger.warning("⚠️ Scheduler already running")
    except Exception as e:
        print(f"❌ Error starting scheduler: {str(e)}")
        logger.error(f"❌ Error starting scheduler: {str(e)}")
        raise

def shutdown_scheduler(scheduler: AsyncIOScheduler):
    """Mematikan scheduler dengan aman."""
    try:
        scheduler.shutdown(wait=False)
        print("✅ Scheduler telah dimatikan dengan aman.")
        logger.info("✅ Scheduler shutdown completed successfully")
    except Exception as e:
        print(f"⚠️  Warning saat mematikan scheduler: {str(e)}")
        logger.warning(f"⚠️ Warning during scheduler shutdown: {str(e)}")
