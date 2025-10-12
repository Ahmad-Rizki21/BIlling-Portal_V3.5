# app/main.py
# --- TAMBAHAN IMPORT UNTUK ACTIVITY LOG ---
import json
import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy import select
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
from .models.system_setting import SystemSetting as SettingModel
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
)
from .routers import settings as settings_router
from .routers import (
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
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================
# --- Middleware Backend to FrontEnd ---
# ==========================================================
origins = [
    "https://billingftth.my.id",  # <-- AKTIFKAN INI untuk akses via browser
    "wss://billingftth.my.id",  # <-- AKTIFKAN INI untuk WebSocket di produksi
    # "http://192.168.222.20",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "tauri://localhost",
    # "http://tauri.localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# --- Middleware untuk Mode Maintenance ---
# ==========================================================
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    # Daftar path yang diizinkan selama maintenance
    allowed_paths = [
        "/api/users/token",  # Izinkan login
        "/api/settings/maintenance",  # Izinkan admin mengubah status maintenance
        "/docs",  # Izinkan akses dokumentasi API
        "/openapi.json",
    ]

    # Jika path request ada di daftar yang diizinkan, lewati pengecekan
    if any(request.url.path.startswith(path) for path in allowed_paths):
        return await call_next(request)

    async with AsyncSessionLocal() as db:
        # Ambil status maintenance dari database dengan query berdasarkan key
        stmt_active = select(SettingModel).where(SettingModel.setting_key == "maintenance_active")
        maintenance_active_setting = (await db.execute(stmt_active)).scalar_one_or_none()
        is_active = maintenance_active_setting and maintenance_active_setting.setting_value.lower() == "true"

        if is_active:
            # Jika maintenance aktif, ambil pesannya
            stmt_message = select(SettingModel).where(SettingModel.setting_key == "maintenance_message")
            maintenance_message_setting = (await db.execute(stmt_message)).scalar_one_or_none()
            message = (
                maintenance_message_setting.setting_value
                if maintenance_message_setting
                else "Sistem sedang dalam perbaikan. Silakan coba lagi nanti."
            )

            # Kembalikan response 503 Service Unavailable
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": message},
            )

    # Jika tidak maintenance, lanjutkan ke request berikutnya
    response = await call_next(request)
    return response


# Pastikan middleware ini ada SEBELUM middleware logging agar request yang diblok tidak tercatat sebagai aktivitas
# ==========================================================


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
        logger.info(f"Xendit webhook body: {req_body_bytes.decode('utf-8') if req_body_bytes else 'Empty body'}")

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
                        log_entry = ActivityLog(
                            user_id=user.id,
                            action=f"{request.method} {request.url.path}",
                            details=details,
                        )
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
# @app.websocket("/ws/notifications")
# async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
#     """WebSocket endpoint untuk notifications real-time."""
#     db = None
#     logger = logging.getLogger("app.websocket")
#     logger.info(f"WebSocket connection attempt with token: {token[:20]}...")

#     try:
#         # Dapatkan database session
#         db_generator = get_db()
#         db = await db_generator.__anext__()

#         # Verifikasi token dan dapatkan user
#         user = await get_user_from_token(token, db)
#         if not user:
#             logger.error("Invalid token provided")
#             await websocket.close(code=4001, reason="Invalid token")
#             return

#         # Connect WebSocket menggunakan manager
#         await manager.connect(websocket, user.id)
#         logger.info(f"WebSocket connected for user {user.id}")

#         try:
#             # Keep connection alive dan handle incoming messages
#             while True:
#                 # Tunggu pesan dari client (bisa berupa ping/pong atau commands)
#                 data = await websocket.receive_text()
#                 logger.debug(f"Received message from user {user.id}: {data}")

#                 # Handle ping/pong untuk keep-alive
#                 if data == "ping":
#                     await websocket.send_text("pong")

#         except WebSocketDisconnect:
#             logger.info(f"WebSocket disconnected for user {user.id}")
#         except Exception as e:
#             logger.error(f"WebSocket error for user {user.id}: {e}")
#         finally:
#             manager.disconnect(user.id)

#     except Exception as e:
#         logger.error(f"WebSocket connection error: {e}")
#         try:
#             await websocket.close(code=4000, reason="Connection error")
#         except Exception as e:
#             #  Cukup log sebagai debug, karena ini bukan error kritis
#             logger.debug(f"Failed to cleanly close WebSocket during final cleanup: {e}")
#     finally:
#         # Tutup database session
#         if db:
#             await db.close()


# Event handler untuk startup aplikasi
@app.on_event("startup")
async def startup_event():
    setup_logging()  # <-- Panggil fungsi setup
    logger = logging.getLogger("app.main")

    # 1. Buat tabel di database
    await create_tables()
    print("Tabel telah diperiksa/dibuat.")

    # 2. Tambahkan tugas-tugas terjadwal
    # Setiap job diberi 'id' unik untuk mencegah duplikasi penjadwalan.
    # 'replace_existing=True' memastikan jika server restart, job lama akan diganti.

    # Membuat invoice baru setiap hari jam 1 pagi untuk H-5 jatuh tempo.
    # scheduler.add_job(job_generate_invoices, 'cron', hour=1, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job", replace_existing=True)

    # Menonaktifkan layanan yang telat bayar setiap hari jam 2 pagi.
    # scheduler.add_job(job_suspend_services, 'cron', hour=2, minute=0, timezone='Asia/Jakarta', id="suspend_services_job", replace_existing=True)

    # Mengirim pengingat pembayaran setiap hari jam 8 pagi.
    # scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job", replace_existing=True)

    # Memverifikasi pembayaran yang mungkin terlewat setiap 15 menit.
    # scheduler.add_job(job_verify_payments, 'interval', minutes=15, id="verify_payments_job", replace_existing=True)

    # Mencoba ulang sinkronisasi Mikrotik yang gagal setiap 5 menit.
    # scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job", replace_existing=True)

    # 3. Mulai scheduler
    scheduler.start()
    print("Scheduler telah dimulai...")
    logger.info("Application startup complete")


# Event handler untuk shutdown aplikasi
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler telah dimatikan.")


# API_PREFIX = os.getenv("API_PREFIX", "")

# Meng-include semua router
app.include_router(pelanggan.router)
app.include_router(user.router)
app.include_router(role.router)
app.include_router(data_teknis.router)
app.include_router(harga_layanan.router)
app.include_router(langganan.router)
app.include_router(sk.router)
app.include_router(paket_layanan.router)
app.include_router(invoice.router)
app.include_router(mikrotik_server.router)
app.include_router(uploads.router)
app.include_router(calculator.router)
# app.include_router(system_log.router)
app.include_router(activity_log.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(permission.router)
app.include_router(report.router)
app.include_router(olt.router)
app.include_router(odp.router)
app.include_router(topology.router)
app.include_router(settings_router.router)
app.include_router(inventory.router)
app.include_router(inventory_status.router)
app.include_router(inventory_type.router)
app.include_router(dashboard_pelanggan.router)


# Endpoint root untuk verifikasi
@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Billing System"}


# Test endpoint untuk webhook
@app.post("/test-webhook")
async def test_webhook(request: Request):
    logger = logging.getLogger("app.test")
    body = await request.body()
    logger.info(f"Test webhook received: {body}")
    return {"status": "received", "body": body.decode() if body else None}
