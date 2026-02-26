# app/routers/telegram_monitor.py
"""
🤖 Telegram AI Monitor Router
================================
API endpoint untuk monitoring billing system via Telegram AI.
Menyediakan endpoint untuk:
- Test koneksi Qwen AI + Telegram
- Trigger laporan manual
- Status monitoring
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.telegram_ai_monitor import (
    test_connection,
    run_daily_report,
    run_error_alert,
    run_invoice_report,
    run_server_health_check,
    get_billing_summary,
    send_telegram_message,
)

logger = logging.getLogger("app.routers.telegram_monitor")

router = APIRouter(
    prefix="/telegram-monitor",
    tags=["Telegram AI Monitor"],
    responses={404: {"description": "Not found"}},
)


@router.get("/test-connection")
async def api_test_connection():
    """
    🧪 Test koneksi ke Qwen AI dan Telegram Bot.
    Berguna untuk verifikasi setup awal.
    """
    try:
        result = await test_connection()
        return {
            "status": "ok",
            "message": "Connection test completed",
            "results": result,
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-report")
async def api_send_report(
    report_type: str = Query(
        default="daily",
        description="Tipe laporan: daily, invoice, error, server",
        regex="^(daily|invoice|error|server)$"
    )
):
    """
    📊 Trigger pengiriman laporan ke Telegram secara manual.
    
    Report types:
    - **daily**: Laporan harian lengkap (billing + log + status)
    - **invoice**: Fokus pada status invoice
    - **error**: Analisis error/warning dari log
    - **server**: Server health check
    """
    try:
        if report_type == "daily":
            await run_daily_report()
        elif report_type == "invoice":
            await run_invoice_report()
        elif report_type == "error":
            await run_error_alert()
        elif report_type == "server":
            await run_server_health_check()
        
        return {
            "status": "ok",
            "message": f"Laporan '{report_type}' telah dikirim ke Telegram",
            "report_type": report_type,
        }
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billing-summary")
async def api_billing_summary():
    """
    📈 Mendapatkan ringkasan billing system tanpa AI analysis.
    Data langsung dari database, bisa digunakan untuk monitoring dashboard.
    """
    try:
        summary = await get_billing_summary()
        return {
            "status": "ok",
            "data": summary,
        }
    except Exception as e:
        logger.error(f"Failed to get billing summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-custom-message")
async def api_send_custom_message(
    message: str = Query(..., description="Pesan custom yang akan dikirim ke Telegram"),
    chat_id: str = Query(default=None, description="Custom chat ID (opsional)")
):
    """
    ✉️ Kirim pesan custom ke Telegram Bot.
    Berguna untuk testing atau notifikasi manual dari admin.
    """
    try:
        sent = await send_telegram_message(message, chat_id=chat_id, parse_mode="")
        return {
            "status": "ok" if sent else "error",
            "message": "Pesan terkirim" if sent else "Gagal mengirim pesan",
        }
    except Exception as e:
        logger.error(f"Failed to send custom message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def telegram_webhook(update: dict):
    """
    📩 Telegram Webhook Endpoint.
    Menerima pesan otomatis dari Telegram saat user chat ke bot.
    """
    from ..services.telegram_ai_monitor import handle_telegram_webhook
    import asyncio
    
    # Run in background agar Telegram tidak timeout nunggu AI
    asyncio.create_task(handle_telegram_webhook(update))
    
    return {"status": "ok"}


@router.get("/set-webhook")
async def api_set_webhook(url: str = Query(..., description="URL publik server Anda (e.g. https://api.anda.com/telegram-monitor/webhook)")):
    """
    🔗 Mendaftarkan URL server Anda ke Telegram agar sistem Chatting berfungsi.
    Gunakan URL yang bisa diakses publik (menggunakan domain/HTTPS).
    """
    import httpx
    from ..services.telegram_ai_monitor import TELEGRAM_BOT_TOKEN
    
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(tg_url, params={"url": url})
            return resp.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
