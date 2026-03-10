from fastapi import APIRouter, Depends, HTTPException, Response, Query
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
import time
import logging
from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from ..schemas.dashboard import (
    DashboardData,
    ChartData,
    RevenueSummary,
    StatCard,
    InvoiceSummary,
    BrandRevenueItem,
    PaketDetail,
    BreakdownItem,
)
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..auth import get_current_active_user
from ..database import get_db, get_connection_pool_status
from ..services.dashboard_service import DashboardService
from ..services.cache_service import get_cache_stats, clear_all_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)

class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int
    total_invoice_count: int
    open_tickets_count: int

@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard data with parallel query execution and caching headers.
    Refactored to use DashboardService for business logic.
    """
    # Browser/Proxy caching (5 menit)
    response.headers["Cache-Control"] = "public, max-age=300" 
    
    start_time = time.time()

    try:
        user_with_role = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
            .where(UserModel.id == current_user.id)
        )
        user = user_with_role.scalar_one_or_none()

        if not user or not user.role:
            return DashboardData()

        user_permissions = {p.name for p in user.role.permissions}
        dashboard_response = DashboardData()

        # Jalankan SEMUA pengambilan data secara paralel via service
        tasks = {}

        if "view_widget_pendapatan_bulanan" in user_permissions:
            tasks["revenue_summary"] = asyncio.create_task(service.get_revenue_summary())

        if "view_widget_statistik_pelanggan" in user_permissions:
            tasks["pelanggan_stats"] = asyncio.create_task(service.get_pelanggan_stat_cards())
            tasks["loyalty_chart"] = asyncio.create_task(service.get_loyalty_chart())

        if "view_widget_statistik_server" in user_permissions:
            tasks["server_stats"] = asyncio.create_task(service.get_mikrotik_status_counts_cached())

        if "view_widget_pelanggan_per_lokasi" in user_permissions:
            tasks["lokasi_chart"] = asyncio.create_task(service.get_lokasi_chart())

        if "view_widget_pelanggan_per_paket" in user_permissions:
            tasks["paket_chart"] = asyncio.create_task(service.get_paket_chart())

        if "view_widget_tren_pertumbuhan" in user_permissions:
            tasks["growth_chart"] = asyncio.create_task(service.get_growth_chart())

        # Always included or common permission
        tasks["invoice_summary_chart"] = asyncio.create_task(service.get_invoice_summary_chart())

        if "view_widget_status_langganan" in user_permissions:
            tasks["status_langganan_chart"] = asyncio.create_task(service.get_status_langganan_chart())

        if "view_widget_alamat_aktif" in user_permissions:
            tasks["pelanggan_per_alamat_chart"] = asyncio.create_task(service.get_pelanggan_per_alamat_chart())

        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            results_map = dict(zip(tasks.keys(), results))

            def get_res(key):
                res = results_map.get(key)
                if isinstance(res, Exception):
                    logger.error(f"Error fetching {key}: {res}")
                    return None
                return res

            dashboard_response.revenue_summary = get_res("revenue_summary")
            dashboard_response.loyalitas_pembayaran_chart = get_res("loyalty_chart")
            dashboard_response.lokasi_chart = get_res("lokasi_chart")
            dashboard_response.paket_chart = get_res("paket_chart")
            dashboard_response.growth_chart = get_res("growth_chart")
            dashboard_response.invoice_summary_chart = get_res("invoice_summary_chart")
            dashboard_response.status_langganan_chart = get_res("status_langganan_chart")
            dashboard_response.pelanggan_per_alamat_chart = get_res("pelanggan_per_alamat_chart")

            # Assemble Stat Cards
            temp_stat_cards = []
            pelanggan_stats = get_res("pelanggan_stats")
            if pelanggan_stats: temp_stat_cards.extend(pelanggan_stats)

            server_stats = get_res("server_stats")
            if server_stats:
                temp_stat_cards.extend([
                    StatCard(title="Total Servers", value=server_stats.get("total", 0), description="Total Mikrotik servers"),
                    StatCard(title="Online Servers", value=server_stats.get("online", 0), description="Servers online"),
                    StatCard(title="Offline Servers", value=server_stats.get("offline", 0), description="Servers offline"),
                ])
            
            dashboard_response.stat_cards = temp_stat_cards

        execution_time = time.time() - start_time
        if execution_time > 2.0:
            logger.warning(f"⚠️ Dashboard response took {execution_time:.2f}s")
        
        return dashboard_response

    except Exception as e:
        logger.error(f"❌ Dashboard failed: {str(e)}", exc_info=True)
        return DashboardData(
            revenue_summary=RevenueSummary(total=0.0, periode="bulan", breakdown=[]),
            stat_cards=[],
            lokasi_chart=ChartData(labels=[], data=[]),
            paket_chart=ChartData(labels=[], data=[]),
            growth_chart=ChartData(labels=[], data=[]),
            invoice_summary_chart=InvoiceSummary(labels=[], total=[], lunas=[], menunggu=[], kadaluarsa=[]),
            status_langganan_chart=ChartData(labels=[], data=[]),
            pelanggan_per_alamat_chart=ChartData(labels=[], data=[]),
            loyalitas_pembayaran_chart=ChartData(labels=[], data=[]),
        )

@router.get("/loyalitas-users-by-segment")
async def get_loyalty_users_by_segment(
    segmen: Optional[str] = None, 
    service: DashboardService = Depends(get_dashboard_service)
):
    """Refactored to use DashboardService."""
    return await service.get_loyalty_users_by_segment(segmen)

@router.get("/sidebar-badges", response_model=SidebarBadgeResponse)
async def get_sidebar_badges(service: DashboardService = Depends(get_dashboard_service)):
    """Refactored to use DashboardService."""
    return await service.get_sidebar_badges()

@router.get("/paket-details", response_model=Dict[str, PaketDetail])
async def get_paket_details(service: DashboardService = Depends(get_dashboard_service)):
    """Refactored to use DashboardService."""
    return await service.get_paket_details()

@router.get("/database-health")
async def get_database_health(current_user: UserModel = Depends(get_current_active_user)):
    """Monitoring database connection pool status."""
    try:
        pool_status = await get_connection_pool_status()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "connection_pool": pool_status,
            "performance_impact": {
                "healthy_connections": pool_status["checked_in"],
                "active_connections": pool_status["checked_out"],
                "available_connections": pool_status["pool_size"] - pool_status["checked_out"],
                "utilization_percent": round(
                    (pool_status["checked_out"] / (pool_status["pool_size"] + pool_status["overflow"])) * 100, 2
                ),
            },
        }
    except Exception as e:
        return {"status": "error", "timestamp": datetime.now().isoformat(), "error": str(e), "connection_pool": None}

@router.get("/api-performance", response_model=dict)
async def get_api_performance_metrics(response: Response, current_user: UserModel = Depends(get_current_active_user)):
    """Monitoring API performance metrics."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "optimization_features": {
            "gzip_compression": "enabled",
            "field_filtering": "enabled",
            "cache_headers": "enabled",
            "response_monitoring": "enabled",
            "in_memory_cache": "enabled",
        },
        "performance_tips": [
            "Dashboard data di-cache selama 5 menit",
            "Monitor X-Response-Size headers",
            "Static data di-cache 1 jam",
        ],
        "optimization_impact": {
            "estimated_size_reduction": "30-70%",
            "estimated_speed_improvement": "40-80%",
        },
    }

@router.get("/cache-stats", response_model=dict)
async def get_cache_statistics(
    response: Response,
    current_user: UserModel = Depends(get_current_active_user),
    clear_cache: bool = Query(False, description="Clear all cache data"),
):
    """Monitoring cache performance."""
    response.headers["Cache-Control"] = "public, max-age=30"
    if clear_cache:
        cleared_count = clear_all_cache()
        return {"status": "success", "action": "cache_cleared", "cleared_items": cleared_count}
    
    cache_stats = get_cache_stats()
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "cache_statistics": cache_stats,
        "cache_health": {
            "hit_rate_status": "Excellent" if cache_stats["hit_rate_percent"] > 80 else "Good",
            "memory_usage": "Healthy" if cache_stats["utilization_percent"] < 80 else "High",
        },
    }

@router.get("/websocket-metrics", response_model=dict)
async def get_websocket_metrics(current_user: UserModel = Depends(get_current_active_user)):
    """Monitoring WebSocket metrics."""
    from ..websocket_manager import manager
    metrics = manager.get_metrics()
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "websocket_metrics": metrics,
    }

@router.get("/invoice-generation-monitor")
async def get_invoice_generation_monitor(
    target_date: str = None,
    current_user: UserModel = Depends(get_current_active_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Refactored to use DashboardService with permission check."""
    from ..config import settings
    user_role_name = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
    if not settings.can_access_widget("invoice_generation_monitor", user_role_name):
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    return await service.get_invoice_generation_monitor(target_date)

@router.get("/future-invoice-projection")
async def get_future_invoice_projection(
    target_date: Optional[str] = None,
    current_user: UserModel = Depends(get_current_active_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Refactored to use DashboardService with permission check."""
    from ..config import settings
    user_role_name = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
    if not settings.can_access_widget("future_invoice_projection", user_role_name):
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    return await service.get_future_invoice_projection(target_date)

def clear_mikrotik_cache():
    """Proxy function for service cache clearing."""
    from ..services.dashboard_service import DashboardService
    # This might need a different approach if we want to clear the global variable in service
    # Since it's a global in the service module, we can import it there.
    from ..services import dashboard_service
    dashboard_service._mikrotik_cache = {"data": None, "timestamp": 0}

def clear_sidebar_cache():
    """Proxy function for service cache clearing."""
    from ..services import dashboard_service
    dashboard_service._sidebar_cache = {"data": None, "timestamp": 0}
