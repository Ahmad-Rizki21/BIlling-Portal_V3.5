# app/main.py
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, engine, get_db
from .routers import (
    pelanggan,
    user,
    role,
    data_teknis,
    harga_layanan,
    paket_layanan,
    langganan,
    invoice,
    mikrotik_server,
    uploads,
    notifications,
    dashboard,
    permission,
    sk,
    calculator,
    report,
    olt,
    odp,
    topology,
    settings,
    inventory, 
    inventory_status, 
    inventory_type,
    dashboard_pelanggan  
    )
from .jobs import (
    job_generate_invoices,
    job_suspend_services,
    job_verify_payments,
    job_send_payment_reminders,
    job_retry_mikrotik_syncs,
    job_update_overdue_invoices,
)
from .logging_config import setup_logging
from .auth import get_user_from_token
from .websocket_manager import manager


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
    # "https://billingftth.my.id",
    # "wss://billingftth.my.id",
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


# Tambahan middleware untuk logging request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("app.middleware")

    # Log semua request yang masuk
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    # Jika ini adalah webhook Xendit, log lebih detail
    if "xendit-callback" in str(request.url):
        body = await request.body()
        logger.info(
            f"Xendit webhook body: {body.decode('utf-8') if body else 'Empty body'}"
        )

        # Rebuild request untuk processing
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest

        # Create new request with body preserved
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)

    response = await call_next(request)

    logger.info(f"Response status: {response.status_code}")
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

    # 2. Tambahkan tugas-tugas ke scheduler untuk berjalan setiap hari
    #    (Ganti 'hour' dan 'minute' sesuai kebutuhan Anda)

    # scheduler.add_job(job_generate_invoices, 'cron', hour=1, minute=0, timezone='Asia/Jakarta') #Real

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # scheduler.add_job(job_suspend_services, 'cron', hour=2, minute=0, timezone='Asia/Jakarta') #Real

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # scheduler.add_job(job_suspend_services, 'interval', minutes=20, id="suspend_services_job")

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # Job ini akan berjalan setiap hari pukul 08:00 pagi
    # scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================

    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # job verifikasi Pembayaran setiap jam, di menit ke-15
    # scheduler.add_job(job_verify_payments, 'cron', hour='*', minute=15, timezone='Asia/Jakarta', id="verify_payments_job") #Cek pembayaran setiap jam menit ke-15.
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================


    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================
    # scheduler.add_job(job_verify_payments, 'interval', minutes=1, id="verify_payments_job")
    # scheduler.add_job(job_verify_payments, 'interval', minutes=20, id="verify_payments_job")
    # ======================================================== INI UNTUK CRONJOB PRODACION & TEST========================================================


    #========================================================= INI UNTUK CRONJOB SYNCRONISE MIKROTIK ====================================================
    #scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job")
    #========================================================= INI UNTUK CRONJOB SYNCRONISE MIKROTIK ====================================================

    #=============================================== INI UNTUK CRONJOB MENCARI STATUS YANG MASIH BELUM DIBAYAR=================================
    # scheduler.add_job(job_update_overdue_invoices, 'cron', hour=0, minute=30, timezone='Asia/Jakarta', id="update_overdue_invoices_job")
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

API_PREFIX = os.getenv("API_PREFIX", "")

# Meng-include semua router
app.include_router(pelanggan.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(role.router, prefix=API_PREFIX)
app.include_router(data_teknis.router, prefix=API_PREFIX)
app.include_router(harga_layanan.router, prefix=API_PREFIX)
app.include_router(langganan.router, prefix=API_PREFIX)
app.include_router(sk.router, prefix=API_PREFIX)
app.include_router(paket_layanan.router, prefix=API_PREFIX)
app.include_router(invoice.router, prefix=API_PREFIX)
app.include_router(mikrotik_server.router, prefix=API_PREFIX)
app.include_router(uploads.router, prefix=API_PREFIX)
app.include_router(calculator.router, prefix=API_PREFIX)
# app.include_router(system_log.router)
# app.include_router(activity_log.router)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(permission.router, prefix=API_PREFIX)
app.include_router(report.router, prefix=API_PREFIX)
app.include_router(olt.router, prefix=API_PREFIX)
app.include_router(odp.router, prefix=API_PREFIX)
app.include_router(topology.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(inventory.router, prefix=API_PREFIX)
app.include_router(inventory_status.router, prefix=API_PREFIX) 
app.include_router(inventory_type.router, prefix=API_PREFIX)   
app.include_router(dashboard_pelanggan.router, prefix=API_PREFIX)


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
