# app/main.py

# --- TAMBAHAN IMPORT UNTUK ACTIVITY LOG ---
import json
import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from . import config
from .auth import get_user_from_token
from .config import settings
from .database import AsyncSessionLocal, Base, engine, get_db
from .jobs import (
    job_generate_invoices,
    job_retry_mikrotik_syncs,
    job_send_payment_reminders,
    job_suspend_services,
    job_verify_payments,
)
from .logging_config import setup_logging
from .models.activity_log import ActivityLog
from .models.user import User as UserModel
from .routers import (
    activity_log,
    calculator,
    dashboard,
    dashboard_pelanggan,
    data_teknis,
    harga_layanan,
    inventory,
    inventory_status,
    inventory_type,
    invoice,
    langganan,
    mikrotik_server,
    notifications,
    odp,
    olt,
    paket_layanan,
    pelanggan,
    permission,
    report,
    role,
    settings,
    sk,
    topology,
    uploads,
    user,
)
from .websocket_manager import manager

# --- AKHIR TAMBAHAN IMPORT ---




# Fungsi untuk membuat tabel di database saat aplikasi pertama kali dijalankan
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Hati-hati, ini akan menghapus semua tabel
        await conn.run_sync(Base.metadata.create_all)

# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title="Billing System API",
    description="API untuk sistem billing terintegrasi Xendit.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================
# --- Middleware Backend to FrontEnd ---
# ==========================================================
origins = [
    "https://billingftth.my.id",
    "wss://billingftth.my.id",
    "http://192.168.222.20",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "tauri://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- FUNGSI BANTU UNTUK MENDAPATKAN USER DARI TOKEN (VERSI AMAN UNTUK LOGGING) ---
async def get_user_from_token_for_logging(token: str, db: AsyncSession) -> UserModel | None:
    """
    Mendekode token dan mengambil data user untuk keperluan logging.
    Fungsi ini aman dan akan mengembalikan None jika terjadi error, tanpa menghentikan aplikasi.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
        user = await db.get(UserModel, int(user_id))
        return user
    except (JWTError, ValueError, TypeError):
        # Menangkap semua kemungkinan error (token tidak valid, user_id bukan angka, dll)
        return None

# ==========================================================
# --- DAFTARKAN ROUTER WEBSOCKET DI SINI (PALING ATAS) ---
# ==========================================================
app.include_router(notifications.router, prefix="/api")
# ==========================================================

# Tambahan middleware untuk logging request
@app.middleware("http")
async def log_requests_and_activity(request: Request, call_next):
    logger = logging.getLogger("app.middleware")
    start_time = time.time()

    # Log semua request yang masuk
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    # --- LOGIKA BARU: BACA BODY REQUEST DI AWAL ---
    # Kita harus membaca body di sini agar bisa digunakan untuk logging nanti.
    req_body_bytes = await request.body()

    # Buat ulang request agar endpoint tetap bisa membaca body-nya.
    async def receive():
        return {"type": "http.request", "body": req_body_bytes, "more_body": False}

    request_with_body = Request(request.scope, receive)
    # --- AKHIR LOGIKA BACA BODY ---

    # Jika ini adalah webhook Xendit, log lebih detail
    if "xendit-callback" in str(request.url):
        logger.info(
            f"Xendit webhook body: {req_body_bytes.decode('utf-8') if req_body_bytes else 'Empty body'}"
        )

    response = await call_next(request_with_body)

    process_time = time.time() - start_time
    logger.info(f"Response status: {response.status_code} in {process_time:.2f}s")

    # --- LOGIKA BARU: SIMPAN ACTIVITY LOG KE DATABASE ---
    if request.method in ["POST", "PATCH", "DELETE"] and 200 <= response.status_code < 300:
        if "/token" not in str(request.url) and "/login" not in str(request.url):
            async with AsyncSessionLocal() as db:
                try:
                    auth_header = request.headers.get("Authorization", "")
                    token = auth_header.replace("Bearer ", "")
                    user = await get_user_from_token_for_logging(token, db)
                    if user:
                        details = None
                        if req_body_bytes:
                            try:
                                details = json.dumps(json.loads(req_body_bytes))
                            except json.JSONDecodeError:
                                # Jika bukan JSON (misal: file upload), catat placeholder
                                details = f"[Data non-JSON, Content-Type: {request.headers.get('content-type')}]"
                        log_entry = ActivityLog(user_id=user.id, action=f"{request.method} {request.url.path}", details=details)
                        db.add(log_entry)
                        await db.commit()
                        logger.info(f"Activity logged for user {user.email}: {log_entry.action}")
                except Exception as e:
                    logger.error(f"Failed to log activity: {e}", exc_info=True)

    return response
# ==========================================================

# Inisialisasi scheduler
scheduler = AsyncIOScheduler()

# Test endpoint untuk WebSocket
@app.get("/ws/test")
def websocket_test():
    return {"message": "WebSocket endpoint accessible", "status": "ok"}

# WebSocket endpoint

# Event handler untuk startup aplikasi
@app.on_event("startup")
async def startup_event():
    setup_logging() # <-- Panggil fungsi setup
    logger = logging.getLogger('app.main')

    # 1. Buat tabel di database
    await create_tables()
    print("Tabel telah diperiksa/dibuat.")

    # 2. Tambahkan tugas-tugas ke scheduler untuk berjalan setiap hari
    #    (Ganti 'hour' dan 'minute' sesuai kebutuhan Anda)
    
    # scheduler.add_job(job_generate_invoices, 'cron', hour=1, minute=0, timezone='Asia/Jakarta') #Real
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # scheduler.add_job(job_suspend_services, 'cron', hour=2, minute=0, timezone='Asia/Jakarta') #Real
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    scheduler.add_job(job_suspend_services, 'interval', minutes=20, id="suspend_services_job")

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # Job ini akan berjalan setiap hari pukul 08:00 pagi
    scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # job verifikasi Pembayaran setiap jam, di menit ke-15
    # scheduler.add_job(job_verify_payments, 'cron', hour='*', minute=15, timezone='Asia/Jakarta', id="verify_payments_job") #Cek pembayaran setiap jam menit ke-15.
    
    #scheduler.add_job(job_verify_payments, 'interval', minutes=1, id="verify_payments_job")
    scheduler.add_job(job_verify_payments, 'interval', minutes=20, id="verify_payments_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================


    #========================================================= INI UNTUK CRONJOB SYNCRONISE MIKROTIK ====================================================
    scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job")
    #========================================================= INI UNTUK CRONJOB SYNCRONISE MIKROTIK ====================================================

    #=============================================== INI UNTUK CRONJOB MENCARI STATUS YANG MASIH BELUM DIBAYAR=================================
    #scheduler.add_job(job_update_overdue_invoices, 'cron', hour=0, minute=30, timezone='Asia/Jakarta', id="update_overdue_invoices_job")
    #=============================================== INI UNTUK CRONJOB MENCARI STATUS YANG MASIH BELUM DIBAYAR=================================


    # 3. Mulai scheduler
    scheduler.start()
    print("Scheduler telah dimulai...")
    logger.info("Application startup complete")

# Event handler untuk shutdown aplikasi
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler telah dimatikan.")

# Meng-include semua router
app.include_router(pelanggan.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(role.router, prefix="/api")
app.include_router(data_teknis.router, prefix="/api")
app.include_router(harga_layanan.router, prefix="/api")
app.include_router(langganan.router, prefix="/api")
app.include_router(sk.router, prefix="/api")
app.include_router(paket_layanan.router, prefix="/api")
app.include_router(invoice.router, prefix="/api")
app.include_router(mikrotik_server.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(calculator.router, prefix="/api")
# app.include_router(system_log.router)
app.include_router(activity_log.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(permission.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(olt.router, prefix="/api")
app.include_router(odp.router, prefix="/api")
app.include_router(topology.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(inventory_status.router, prefix="/api")
app.include_router(inventory_type.router, prefix="/api")
app.include_router(dashboard_pelanggan.router, prefix="/api")

# Endpoint root untuk verifikasi
@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Billing System"}

# Test endpoint untuk webhook
@app.post("/test-webhook")
async def test_webhook(request: Request):
    logger = logging.getLogger('app.test')
    body = await request.body()
    logger.info(f"Test webhook received: {body}")
    return {"status": "received", "body": body.decode() if body else None}
