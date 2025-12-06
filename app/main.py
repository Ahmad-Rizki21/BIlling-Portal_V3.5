# ====================================================================
# MAIN APPLICATION - SISTEM BILLING FTTH
# ====================================================================
# File ini adalah pintu gerbang utama aplikasi billing sistem untuk
# layanan internet Fiber To The Home (FTTH). Menggunakan FastAPI
# sebagai backend framework.
#
# Fitur utama:
# - RESTful API untuk manajemen pelanggan, billing, dan layanan
# - WebSocket untuk notifikasi real-time
# - Auto-generation invoice dan penjadwalan tugas
# - Integrasi payment gateway (Xendit)
# - Manajemen user dan permission
# - Logging aktivitas sistem
# ====================================================================

import json
import logging
import os
import time
from datetime import datetime

# Library untuk scheduling (auto-jobs)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError

# FastAPI core components
from fastapi import FastAPI, Query, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

# JWT token handling
from jose import JWTError, jwt

# Database components
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import modul-modul lokal
from . import config
from .auth import get_user_from_token
from .config import settings
from .database import AsyncSessionLocal, Base, engine, get_db, init_encryption


# Import job-job terjadwal (auto-invoice, suspend, dll)
from .jobs import (
    job_generate_invoices,      # Auto generate invoice H-5 jatuh tempo
    job_retry_failed_invoices,  # Retry invoice yang gagal dibuat payment link
    job_retry_mikrotik_syncs,   # Retry sync mikrotik yang gagal
    job_send_payment_reminders, # Kirim reminder pembayaran
    job_suspend_services,       # Suspend layanan telat bayar
    job_verify_payments,        # Verifikasi pembayaran masuk
)

# Import untuk logging
from .logging_config import setup_logging

# Import models (database tables)
from .models.activity_log import ActivityLog
from .models.system_setting import SystemSetting as SettingModel
from .models.user import User as UserModel

# Import semua router (API endpoints)
from .routers import (
    activity_log,      # Log aktivitas user
    auth,              # Authentication & authorization
    calculator,        # Kalkulator biaya
    dashboard,         # Dashboard admin
    dashboard_pelanggan, # Dashboard pelanggan
    data_teknis,       # Data teknis koneksi
    global_search,     # Global search functionality
    harga_layanan,     # Harga paket layanan
    inventory,         # Manajemen inventory
    inventory_status,  # Status inventory
    inventory_type,    # Tipe inventory
    invoice,           # Manajemen invoice/tagihan
    langganan,         # Manajemen langganan pelanggan
    mikrotik_server,   # Konfigurasi Mikrotik
    notifications,     # Sistem notifikasi
    odp,               # ODP (Optical Distribution Point)
    olt,               # OLT (Optical Line Terminal)
    paket_layanan,     # Paket-paket layanan
    pelanggan,         # Data pelanggan
    permission,        # Manajemen permission
    report,            # Laporan-laporan
    role,              # Role-based access control
    trouble_ticket,    # Sistem trouble ticket
)
from .routers import settings as settings_router  # Pengaturan sistem
from .routers import (
    sk,                # Syarat & Ketentuan
    topology,          # Topologi jaringan
    traffic_monitoring, # Traffic monitoring PPPoE
    uploads,           # Upload file管理
)
from .routers import rate_limiter_monitor  # Rate limiter monitoring
from .routers import user  # User management
from .routers import error_report  # Error reporting system

# WebSocket manager untuk notifikasi real-time
from .websocket_manager import manager


# ====================================================================
# DATABASE INITIALIZATION
# ====================================================================

async def create_tables():
    """
    Buat semua tabel di database saat aplikasi pertama kali jalan.
    Fungsi ini otomatis membuat tabel berdasarkan model yang sudah didefinisikan.
    WARNING: Jangan uncomment drop_all() kecuali mau reset semua data!
    """
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # ⚠️ HATI-HATI: Hapus semua tabel!
        await conn.run_sync(Base.metadata.create_all)  # Buat tabel jika belum ada


# ====================================================================
# FASTAPI APP INITIALIZATION
# ====================================================================

# Inisialisasi aplikasi FastAPI utama
app = FastAPI(
    title="Billing System API",
    description="API sistem billing FTTH terintegrasi dengan payment gateway Xendit",
    version="1.0.0",
    docs_url="/docs",           # Swagger UI documentation
    redoc_url="/redoc",         # ReDoc documentation
)

# Mount static files directory (buat file-file static kayak image, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount directory buat file evidence (bukti) upload
evidence_dir = os.path.join(os.getcwd(), "static", "uploads", "evidence")
os.makedirs(evidence_dir, exist_ok=True)  # Buat folder kalo belum ada
app.mount("/static/uploads/evidence", StaticFiles(directory=evidence_dir), name="evidence")


# Mount evidence files at /api path for frontend compatibility
#app.mount("/api/static/uploads/evidence", StaticFiles(directory=evidence_dir), name="evidence_api")

# ==========================================================
# --- Middleware Backend to FrontEnd ---
# ==========================================================
origins = [
    "https://billingftth.my.id",  # <-- AKTIFKAN INI untuk akses via browser
    "wss://billingftth.my.id",  # <-- AKTIFKAN INI untuk WebSocket di produksi
    # "http://192.168.222.20",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "ws://localhost:3000",
    "ws://127.0.0.1:3000",
    "tauri://localhost",
    "http://localhost:8000",  # Backend origin
    "http://127.0.0.1:8000",  # Backend origin
    "*",  # Allow all origins for development
]

# Add GZip compression untuk response yang lebih kecil
# Middleware untuk cache headers
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)

        # Cache static files untuk 1 tahun
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # Cache API response untuk 5 menit (kecuali POST/PUT/DELETE)
        elif request.method in ["GET"] and request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "public, max-age=300"

        return response

app.add_middleware(CacheControlMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


# ==========================================================
# --- Middleware untuk Mode Maintenance ---
# ==========================================================
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    # Daftar path yang diizinkan selama maintenance
    allowed_paths = [
        "/auth/token",  # Izinkan login
        "/auth/refresh",  # Izinkan refresh token
        "/auth/logout",  # Izinkan logout
        "/users/token",  # Izinkan login (backup path)
        "/pelanggan",  # Izinkan akses pelanggan
        "/paket_layanan",  # Izinkan akses paket layanan
        "/harga_layanan",  # Izinkan akses harga layanan
        "/settings/maintenance",  # Izinkan admin mengubah status maintenance
        "/docs",  # Izinkan akses dokumentasi API
        "/openapi.json",
        "/ws/test",  # Izinkan WebSocket test
    ]

    # Jika path request ada di daftar yang diizinkan, lewati pengecekan
    if any(request.url.path.startswith(path) for path in allowed_paths):
        return await call_next(request)

    async with AsyncSessionLocal() as db:  # type: ignore[attr-defined]
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
            async with AsyncSessionLocal() as db:  # type: ignore[attr-defined]
                try:
                    auth_header = request.headers.get("Authorization", "")
                    token = auth_header.replace("Bearer ", "")
                    user = await get_user_from_token_for_logging(token, db)
                    if user:
                        details = None
                        if req_body_bytes:
                            try:
                                # Hanya coba decode JSON untuk content-type application/json
                                content_type = request.headers.get('content-type', '')
                                if 'application/json' in content_type:
                                    details = json.dumps(json.loads(req_body_bytes.decode('utf-8')))
                                else:
                                    # Skip JSON parsing untuk non-JSON content (file uploads, etc.)
                                    details = f"[Binary data, Content-Type: {content_type}]"
                            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
                                # Tangkap berbagai jenis decode error
                                details = f"[Parse error - {str(e)}, Content-Type: {request.headers.get('content-type')}"
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


# Test endpoint untuk token validation
@app.get("/api/ws/token-test")
async def test_token_validation(request: Request):
    """Test endpoint untuk debugging token validation."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "No Bearer token provided"}

    token = auth_header.replace("Bearer ", "")

    # Test token validation
    from .auth import verify_access_token
    try:
        payload = verify_access_token(token)
        return {
            "status": "valid",
            "payload": {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            },
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }
    except Exception as e:
        return {
            "status": "invalid",
            "error": str(e),
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }


# Endpoint untuk refresh token WebSocket
@app.post("/api/ws/refresh-token")
async def refresh_websocket_token(request: Request):
    """Endpoint untuk refresh token WebSocket connection."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "No Bearer token provided"}

    refresh_token = auth_header.replace("Bearer ", "")

    async with AsyncSessionLocal() as db:  # type: ignore[attr-defined]
        try:
            from .auth import verify_access_token, create_access_token
            from datetime import timedelta

            # Verify refresh token
            payload = verify_access_token(refresh_token)

            # Check if this is a refresh token type
            if payload.get("type") != "refresh":
                return {"error": "Invalid refresh token"}

            user_id = payload.get("sub")
            if not user_id:
                return {"error": "Invalid token payload"}

            # Get user from database
            user = await db.get(UserModel, int(user_id))
            if not user:
                return {"error": "User not found"}

            # Create new access token
            new_access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email},
                expires_delta=timedelta(minutes=120)  # 2 hours
            )

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 7200,  # 2 hours in seconds
                "message": "Token refreshed successfully"
            }

        except Exception as e:
            logger = logging.getLogger("app.websocket")
            logger.error(f"Token refresh failed: {e}")
            return {"error": "Token refresh failed", "detail": str(e)}


# Endpoint untuk monitoring active WebSocket connections
@app.get("/api/ws/status")
async def websocket_status():
    """Monitor active WebSocket connections."""
    metrics = manager.get_metrics()
    active_connections = list(manager.active_connections.keys())

    # Get connection metadata
    connection_details = {}
    for user_id in active_connections:
        if user_id in manager.connection_metadata:
            metadata = manager.connection_metadata[user_id]
            connection_details[user_id] = {
                "connected_at": metadata.get("connected_at", 0),
                "last_activity": metadata.get("last_activity", 0),
                "messages_sent": metadata.get("messages_sent", 0),
                "roles": list(manager.user_roles.get(user_id, []))
            }

    return {
        "metrics": metrics,
        "active_connections": active_connections,
        "connection_details": connection_details,
        "total_active": len(active_connections),
        "rate_limit_status": {
            "blocked_ips": len([ip for ip, attempts in manager.connection_attempts.items() if len(attempts) >= manager.max_attempts_per_window]),
            "total_tracked_ips": len(manager.connection_attempts)
        }
    }


# Admin endpoint untuk clear rate limit (emergency use only)
@app.post("/api/ws/clear-rate-limit")
async def clear_rate_limit(request: Request):
    """Clear rate limit for specific IP (admin only)."""
    data = await request.json()
    client_ip = data.get("ip")

    if not client_ip:
        return {"error": "IP address required"}

    # Simple security check - only allow from trusted IPs
    client_real_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    trusted_ips = ["127.0.0.1", "localhost", "::1", "192.168.222.20"]  # Add your trusted IPs

    if client_real_ip not in trusted_ips:
        logger = logging.getLogger("app.websocket")
        logger.warning(f"Unauthorized rate limit clear attempt from IP: {client_real_ip}")
        return {"error": "Unauthorized"}

    manager.clear_rate_limit(client_ip)
    return {"message": f"Rate limit cleared for IP {client_ip}"}


# WebSocket endpoint untuk notifications
# Path: /ws/notifications (langsung di main.py sesuai konfigurasi Apache)
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint untuk notifications real-time."""
    db = None
    endpoint_name = "main.py"
    logger = logging.getLogger("app.websocket")

    # Get client IP for rate limiting
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"[{endpoint_name}] WebSocket connection attempt from IP: {client_ip} with token: {token[:20] if len(token) > 20 else token}...")

    # Check rate limiting
    if manager.is_rate_limited(client_ip):
        logger.warning(f"[{endpoint_name}] Rate limit exceeded for IP {client_ip}")
        await websocket.close(code=4408, reason="Too many connection attempts. Please wait before trying again.")
        return

    try:
        # Validasi token awal
        if not token:
            logger.warning(f"[{endpoint_name}] No token provided")
            await websocket.close(code=4001, reason="Token required")
            return

        logger.info(f"[{endpoint_name}] Token received, attempting validation...")

        # Dapatkan database session
        db_generator = get_db()
        db = await db_generator.__anext__()

        # Verifikasi token dan dapatkan user
        user = await get_user_from_token(token, db)
        if not user:
            # Handle URL encoded token
            import urllib.parse
            try:
                decoded_token = urllib.parse.unquote(token)
            except Exception:
                decoded_token = token

            # Log detail token untuk debugging (hanya sebagian untuk security)
            token_preview = decoded_token[:20] + "..." if len(decoded_token) > 20 else decoded_token
            logger.warning(f"[{endpoint_name}] Invalid token provided - Token preview: {token_preview}, Length: {len(decoded_token)}")

            # Coba decode token untuk melihat expiry dan beri feedback yang lebih berguna
            try:
                from .auth import verify_access_token
                payload = verify_access_token(decoded_token)
                exp = payload.get('exp', 'unknown')
                exp_time = datetime.fromtimestamp(exp) if isinstance(exp, (int, float)) else 'unknown'
                logger.warning(f"[{endpoint_name}] Token decode successful but user not found. Expiry: {exp_time}")

                # Kirim pesan error yang lebih informatif ke client
                await websocket.close(code=4401, reason="Token valid but user not found - Please refresh your page and login again")
            except Exception as decode_error:
                error_type = type(decode_error).__name__
                logger.warning(f"[{endpoint_name}] Token decode failed ({error_type}): {str(decode_error)}")

                # Berikan pesan error yang lebih spesifik berdasarkan tipe error
                if "expired" in str(decode_error).lower():
                    await websocket.close(code=4401, reason="Token expired - Please refresh your page and login again")
                elif "signature" in str(decode_error).lower():
                    await websocket.close(code=4400, reason="Token signature invalid - Please refresh your page and login again")
                else:
                    await websocket.close(code=4400, reason="Invalid token format - Please refresh your page and login again")
            return

        logger.info(f"[{endpoint_name}] Authentication successful: {user.name} (ID: {user.id}, Email: {user.email})")

        # Connect WebSocket menggunakan manager
        await manager.connect(websocket, user.id)
        logger.info(f"[{endpoint_name}] Connection established for user {user.id} from IP {client_ip}")

        # Kirim pesan konfirmasi ke client
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "WebSocket connected successfully",
            "user_id": user.id,
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "active_connections": len(manager.active_connections),
                "user_roles": list(manager.user_roles.get(user.id, []))
            }
        }))

        try:
            # Keep connection alive dan handle incoming messages
            while True:
                # Tunggu pesan dari client
                data = await websocket.receive_text()
                log_message = data[:100] + "..." if len(data) > 100 else data
                logger.debug(f"[{endpoint_name}] Message from user {user.id}: {log_message}")

                # Handle ping/pong untuk keep-alive
                if data.lower() == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    continue

                # Handle JSON commands
                try:
                    msg_data = json.loads(data)
                    command = msg_data.get("command")

                    if command == "get_status":
                        await websocket.send_text(json.dumps({
                            "type": "status_response",
                            "status": "connected",
                            "user_id": user.id,
                            "timestamp": datetime.now().isoformat()
                        }))

                except json.JSONDecodeError:
                    logger.warning(f"[{endpoint_name}] Non-JSON message from user {user.id}: {log_message}")

        except WebSocketDisconnect:
            logger.info(f"[{endpoint_name}] WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(f"[{endpoint_name}] WebSocket error for user {user.id}: {e}")
        finally:
            await manager.disconnect(user.id)

    except Exception as e:
        logger.error(f"[{endpoint_name}] WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Connection error")
        except Exception as e:
            logger.debug(f"[{endpoint_name}] Failed to cleanly close WebSocket during final cleanup: {e}")
    finally:
        # Tutup database session
        if db:
            await db.close()


# Event handler untuk startup aplikasi
@app.on_event("startup")
async def startup_event():
    setup_logging()  # <-- Panggil fungsi setup
    logger = logging.getLogger("app.main")

    # 1. Buat tabel di database
    await create_tables()
    print("Tabel telah diperiksa/dibuat.")

    # 2. Inisialisasi enkripsi/dekripsi untuk data sensitif
    init_encryption()
    print("Enkripsi/Deskripsi data sensitif telah diinisialisasi.")

    # 3. Tambahkan tugas-tugas terjadwal
    # Setiap job diberi 'id' unik untuk mencegah duplikasi penjadwalan.
    # 'replace_existing=True' memastikan jika server restart, job lama akan diganti.

    #==============================================================GENERATE INVOICE====================================================================================#
    # Generate invoice setiap hari jam 10:00 pagi untuk langganan yang jatuh tempo 5 hari lagi (H-5).
    #scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job", replace_existing=True)
    #==============================================================GENERATE INVOICE====================================================================================#

    #==============================================================SUSPANDED AND UNSUSPANDED=======================================================================#
    # Suspend services tepat tanggal 5 jam 00:00 untuk pelanggan yang telat bayar dari jatuh tempo tanggal 1.
    # Updated: Gunakan location-based batch suspend untuk optimal performance
    # from .jobs import job_suspend_services_by_location
    # scheduler.add_job(
    #     job_suspend_services_by_location,
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
    #==============================================================SUSPANDED AND UNSUSPANDED=======================================================================#

    #==============================================================REMAINDERS INVOICE=======================================================================#
    # Mengirim pengingat pembayaran setiap hari jam 8 pagi.
    #scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job", replace_existing=True)
    #==============================================================REMAINDERS INVOICE=======================================================================#

    #==============================================================NYARI INVOICE 3 HARI KE BELAKANG JIKA SERVER MATI=======================================================================#
    # Memverifikasi pembayaran yang mungkin terlewat setiap 15 menit.
    #from .jobs import job_verify_payments
    #scheduler.add_job(job_verify_payments, 'interval', minutes=15, id="verify_payments_job", replace_existing=True, max_instances=1)
    #==============================================================NYARI INVOICE 3 HARI KE BELAKANG JIKA SERVER MATI=======================================================================#


    #==============================================================SINGKRONISASI PROSES MIKROTIK KE SERVER=======================================================================#
    # Mencoba ulang sinkronisasi Mikrotik yang gagal setiap 5 menit.
    #from .jobs import job_retry_mikrotik_syncs
    #scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job", replace_existing=True, max_instances=1)
    #==============================================================SINGKRONISASI PROSES MIKROTIK KE SERVER=======================================================================#


    #==============================================================MENGULANG PROSES INVOICEING JIKA GAGAL=======================================================================#
    # Retry invoice yang gagal dibuat payment link setiap 1 jam
    #scheduler.add_job(job_retry_failed_invoices, 'interval', hours=1, id="retry_failed_invoices_job", replace_existing=True)
    #==============================================================MENGULANG PROSES INVOICEING JIKA GAGAL=======================================================================#

    #==============================================================COLLECT TRAFFIC DARI MIKROTIK=======================================================================#
    # 5. Setup traffic monitoring jobs
    # from .jobs_traffic import setup_traffic_monitoring_jobs
    # setup_traffic_monitoring_jobs(scheduler)
    #==============================================================COLLECT TRAFFIC DARI MIKROTIK=======================================================================#

    # Log scheduler info
    # print("="*80)
    # print("📅 SCHEDULED JOBS STATUS")
    # print("="*80)
    # print("✅ Invoice Generation: menggunakan H-5 system")
    # print("✅ Location-Based Batch Suspend: Setiap tanggal 5 jam 00:00 WIB")
    # print("✅ Payment Reminders: Diaktifkan tanggal 4")
    # print("✅ Payment Verification: Setiap 15 menit")
    # print("✅ Mikrotik Sync Retry: Setiap 5 menit")
    # print("✅ Payment Link Retry: Setiap 1 jam")
    # print("ℹ️ Traffic Monitoring: Dinonaktifkan")
    # print("="*80)

    # # 6. Mulai scheduler dengan safety check
    # try:
    #     scheduler.start()
    #     print("🚀 Scheduler telah dimulai dengan Location-Based Batch Suspend!")
    #     logger.info("✅ Application startup complete - Location-Based Batch Suspend Active")
    # except SchedulerAlreadyRunningError:
    #     print("⚠️  Scheduler sudah berjalan, melanjutkan dengan instance yang ada...")
    #     logger.warning("⚠️ Scheduler already running, continuing with existing instance")
    # except Exception as e:
    #     print(f"❌ Error starting scheduler: {str(e)}")
    #     logger.error(f"❌ Error starting scheduler: {str(e)}")
    #     raise


# Event handler untuk shutdown aplikasi
@app.on_event("shutdown")
async def shutdown_event():
    try:
        scheduler.shutdown(wait=False)
        print("✅ Scheduler telah dimatikan dengan aman.")
        logger.info("✅ Scheduler shutdown completed successfully")
    except Exception as e:
        print(f"⚠️  Warning saat mematikan scheduler: {str(e)}")
        logger.warning(f"⚠️ Warning during scheduler shutdown: {str(e)}")


# API_PREFIX = os.getenv("API_PREFIX", "")

# Meng-include semua router
app.include_router(pelanggan.router)
app.include_router(user.router)
app.include_router(role.router)
app.include_router(auth.router)
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
app.include_router(global_search.router)
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
app.include_router(trouble_ticket.router)
app.include_router(traffic_monitoring.router)
app.include_router(rate_limiter_monitor.router)
app.include_router(error_report.router)



# Endpoint root untuk verifikasi
@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Billing System"}


# Health Check Endpoint untuk monitoring
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint untuk monitoring server status.
    Digunakan oleh frontend untuk mengecek apakah backend online.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Artacom FTTH Billing System",
        "version": "1.0.0"
    }


# Health Check endpoint dengan /api prefix untuk frontend compatibility
@app.get("/api/health")
async def health_check_api():
    """
    Health check endpoint dengan /api prefix.
    Memastikan frontend bisa mengecek status backend dengan mudah.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Artacom FTTH Billing System",
        "version": "1.0.0",
        "api_version": "v1"
    }


# ====================================================================
# CUSTOM 404 ERROR HANDLER
# ====================================================================
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Custom handler untuk 404 Not Found errors.
    Memberikan response yang informatif untuk client yang mengakses endpoint yang tidak ada.
    """
    import logging
    logger = logging.getLogger("app.error_handler")

    # Log 404 error untuk monitoring
    logger.warning(f"404 Error - Path: {request.url.path} - Method: {request.method} - IP: {request.client.host if request.client else 'unknown'}")

    # Response format yang konsisten
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint tidak ditemukan",
                "description": f"URL '{request.method} {request.url.path}' tidak tersedia di API ini",
                "suggestions": [
                    "Periksa kembali URL yang Anda ketik",
                    "Lihat dokumentasi API di /docs atau /redoc",
                    "Pastikan method HTTP yang digunakan benar (GET, POST, PUT, DELETE)",
                    "Hubungi IT Support jika masalah berlanjut"
                ],
                "available_endpoints": {
                    "docs": "/docs (Swagger UI)",
                    "redoc": "/redoc (ReDoc)",
                    "health": "/ (Health Check)",
                    "auth": "/auth/token (Authentication)",
                    "common_api": [
                        "/pelanggan",
                        "/langganan",
                        "/invoices",
                        "/dashboard",
                        "/mikrotik",
                        "/reports"
                    ]
                },
                "timestamp": datetime.now().isoformat(),
                "request_id": f"404-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        },
        headers={"Content-Type": "application/json"}
    )


# ====================================================================
# GLOBAL EXCEPTION HANDLER
# ====================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler untuk menangkap semua error yang tidak tertangani.
    Memberikan response yang aman dan informatif tanpa exposing internal details.
    """
    import logging
    logger = logging.getLogger("app.error_handler")

    # Generate error ID untuk tracking
    error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(exc) % 10000:04d}"

    # Log error detail untuk debugging
    logger.error(
        f"Unhandled Exception - ID: {error_id} - Path: {request.url.path} - Error: {str(exc)}",
        exc_info=True,
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )

    # Response yang aman untuk client
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Terjadi kesalahan pada server",
                "description": "Sistem sedang mengalami gangguan. Silakan coba lagi beberapa saat.",
                "error_id": error_id,
                "suggestions": [
                    "Refresh halaman dan coba lagi",
                    "Periksa koneksi internet Anda",
                    "Hubungi IT Support dengan menyebutkan Error ID ini",
                    "Coba kembali dalam beberapa menit"
                ],
                "timestamp": datetime.now().isoformat()
            }
        },
        headers={"Content-Type": "application/json"}
    )


# Test endpoint untuk webhook
@app.post("/test-webhook")
async def test_webhook(request: Request):
    logger = logging.getLogger("app.test")
    body = await request.body()
    logger.info(f"Test webhook received: {body.decode() if body else 'Empty body'}")
    return {"status": "received", "body": body.decode() if body else None}
