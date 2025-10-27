# ====================================================================
# TRAFFIC MONITORING ROUTER - PPPoE BANDWIDTH MONITORING API
# ====================================================================
# Router ini menyediakan endpoints untuk monitoring traffic PPPoE user.
# Menggunakan traffic monitoring service untuk data collection dan analysis.
#
# Endpoints:
# - GET /traffic/monitoring/latest - Get latest traffic data
# - GET /traffic/monitoring/user/{user_id} - Get user traffic history
# - GET /traffic/monitoring/server/{server_id} - Get server traffic summary
# - POST /traffic/monitoring/collect - Manual trigger traffic collection
# - GET /traffic/monitoring/dashboard - Dashboard data summary
#
# Features:
# - Real-time traffic data
# - Historical analysis
# - Server-wise monitoring
# - User-specific tracking
# - Bandwidth trend analysis
# ====================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

from ..database import get_db
from ..models.traffic_history import TrafficHistory
from ..models.data_teknis import DataTeknis
from ..models.mikrotik_server import MikrotikServer
from ..models.pelanggan import Pelanggan
from ..services.traffic_monitoring_service import traffic_monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traffic/monitoring", tags=["Traffic Monitoring"])


# ====================================================================
# SCHEMAS FOR API RESPONSE
# ====================================================================

from pydantic import BaseModel, Field
from typing import Optional


class TrafficDataResponse(BaseModel):
    id: int
    data_teknis_id: int
    username_pppoe: str
    ip_address: str
    rx_mbps: float
    tx_mbps: float
    total_mbps: float
    uptime_seconds: int
    is_active: bool
    timestamp: datetime
    pelanggan_name: Optional[str] = None
    server_name: Optional[str] = None
    olt: Optional[str] = None

    class Config:
        from_attributes = True


class TrafficHistoryResponse(BaseModel):
    timestamp: datetime
    rx_mbps: float
    tx_mbps: float
    total_mbps: float
    uptime_seconds: int

    class Config:
        from_attributes = True


class TrafficSummaryResponse(BaseModel):
    server_id: int
    server_name: str
    active_users: int
    avg_mbps: float
    max_mbps: float
    total_mbps: float
    load_percentage: float = Field(default=0.0, description="Server load percentage")


class DashboardSummaryResponse(BaseModel):
    total_active_users: int
    total_bandwidth_usage: float
    top_consumers: List[TrafficDataResponse]
    server_summary: List[TrafficSummaryResponse]
    collection_status: Dict[str, Any]
    last_updated: datetime


class CollectionResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


# ====================================================================
# API ENDPOINTS
# ====================================================================

@router.get("/latest", response_model=List[TrafficDataResponse])
async def get_latest_traffic_data(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    server_id: Optional[int] = Query(None, description="Filter by Mikrotik server"),
    olt_filter: Optional[str] = Query(None, description="Filter by OLT"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest traffic data untuk dashboard.
    Support filtering by server dan OLT.
    """
    try:
        # Build base query dengan proper joins untuk avoid async issues
        query = select(
            TrafficHistory,
            DataTeknis,
            MikrotikServer,
            Pelanggan
        ).join(
            DataTeknis, TrafficHistory.data_teknis_id == DataTeknis.id
        ).outerjoin(
            MikrotikServer, TrafficHistory.mikrotik_server_id == MikrotikServer.id
        ).outerjoin(
            Pelanggan, DataTeknis.pelanggan_id == Pelanggan.id
        ).where(
            TrafficHistory.is_latest == True
        )

        # Apply filters
        if server_id:
            query = query.where(TrafficHistory.mikrotik_server_id == server_id)

        if olt_filter:
            query = query.where(DataTeknis.olt.like(f'%{olt_filter}%'))

        # Order by total bandwidth descending
        query = query.order_by(desc(TrafficHistory.total_mbps)).limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Format response
        response_data = []
        for traffic, data_teknis, server, pelanggan in rows:
            response_data.append(TrafficDataResponse(
                id=traffic.id,
                data_teknis_id=traffic.data_teknis_id,
                username_pppoe=traffic.username_pppoe,
                ip_address=traffic.ip_address,
                rx_mbps=round(traffic.rx_mbps, 2),
                tx_mbps=round(traffic.tx_mbps, 2),
                total_mbps=round(traffic.total_mbps, 2),
                uptime_seconds=traffic.uptime_seconds,
                is_active=traffic.is_active,
                timestamp=traffic.timestamp,
                pelanggan_name=pelanggan.nama if pelanggan else None,
                server_name=server.name if server else None,
                olt=data_teknis.olt if data_teknis else None
            ))

        return response_data

    except Exception as e:
        logger.error(f"Error getting latest traffic data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get traffic data: {str(e)}"
        )


@router.get("/user/{data_teknis_id}", response_model=List[TrafficHistoryResponse])
async def get_user_traffic_history(
    data_teknis_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get traffic history untuk user tertentu.
    Default 24 jam, max 7 hari.
    """
    try:
        # Verify user exists
        user_query = select(DataTeknis).where(DataTeknis.id == data_teknis_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get traffic history dengan direct query
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        history_query = select(TrafficHistory).where(
            and_(
                TrafficHistory.data_teknis_id == data_teknis_id,
                TrafficHistory.timestamp >= since_time
            )
        ).order_by(desc(TrafficHistory.timestamp))

        history_result = await db.execute(history_query)
        history_records = history_result.scalars().all()

        # Format response
        response_data = []
        for record in history_records:
            response_data.append(TrafficHistoryResponse(
                timestamp=record.timestamp,
                rx_mbps=round(record.rx_mbps, 2),
                tx_mbps=round(record.tx_mbps, 2),
                total_mbps=round(record.total_mbps, 2),
                uptime_seconds=record.uptime_seconds
            ))

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user traffic history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get traffic history: {str(e)}"
        )


@router.get("/server/{server_id}", response_model=List[TrafficSummaryResponse])
async def get_server_traffic_summary(
    server_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get traffic summary untuk server tertentu.
    """
    try:
        # Get server summary data dengan direct query
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        summary_query = select(
            TrafficHistory.mikrotik_server_id.label('server_id'),
            MikrotikServer.name.label('server_name'),
            func.count(TrafficHistory.id).label('active_users'),
            func.avg(TrafficHistory.total_mbps).label('avg_mbps'),
            func.max(TrafficHistory.total_mbps).label('max_mbps'),
            func.sum(TrafficHistory.total_mbps).label('total_mbps')
        ).join(
            MikrotikServer, TrafficHistory.mikrotik_server_id == MikrotikServer.id
        ).where(
            and_(
                TrafficHistory.mikrotik_server_id == server_id,
                TrafficHistory.is_latest == True,
                TrafficHistory.timestamp >= since_time
            )
        ).group_by(
            TrafficHistory.mikrotik_server_id,
            MikrotikServer.name
        )

        summary_result = await db.execute(summary_query)
        summary_rows = summary_result.all()

        # Format response
        response_data = []
        for row in summary_rows:
            # Calculate load percentage (assuming 100Mbps = 100%)
            max_bandwidth = 100  # 100Mbps
            total_mbps = float(row.total_mbps) if row.total_mbps else 0
            load_percentage = min((total_mbps / max_bandwidth) * 100, 100)

            response_data.append(TrafficSummaryResponse(
                server_id=row.server_id,
                server_name=row.server_name,
                active_users=row.active_users,
                avg_mbps=round(float(row.avg_mbps), 2) if row.avg_mbps else 0,
                max_mbps=round(float(row.max_mbps), 2) if row.max_mbps else 0,
                total_mbps=round(total_mbps, 2),
                load_percentage=round(load_percentage, 1)
            ))

        return response_data

    except Exception as e:
        logger.error(f"Error getting server traffic summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server summary: {str(e)}"
        )


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard summary data.
    """
    try:
        # Get latest traffic data dengan proper joins
        latest_query = select(
            TrafficHistory,
            DataTeknis,
            MikrotikServer,
            Pelanggan
        ).join(
            DataTeknis, TrafficHistory.data_teknis_id == DataTeknis.id
        ).outerjoin(
            MikrotikServer, TrafficHistory.mikrotik_server_id == MikrotikServer.id
        ).outerjoin(
            Pelanggan, DataTeknis.pelanggan_id == Pelanggan.id
        ).where(
            TrafficHistory.is_latest == True
        ).order_by(
            desc(TrafficHistory.total_mbps)
        ).limit(20)

        latest_result = await db.execute(latest_query)
        latest_rows = latest_result.all()

        # Get server summaries dengan direct query
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        server_summary_query = select(
            TrafficHistory.mikrotik_server_id.label('server_id'),
            MikrotikServer.name.label('server_name'),
            func.count(TrafficHistory.id).label('active_users'),
            func.avg(TrafficHistory.total_mbps).label('avg_mbps'),
            func.max(TrafficHistory.total_mbps).label('max_mbps'),
            func.sum(TrafficHistory.total_mbps).label('total_mbps')
        ).join(
            MikrotikServer, TrafficHistory.mikrotik_server_id == MikrotikServer.id
        ).where(
            and_(
                TrafficHistory.is_latest == True,
                TrafficHistory.timestamp >= since_time
            )
        ).group_by(
            TrafficHistory.mikrotik_server_id,
            MikrotikServer.name
        )

        server_summary_result = await db.execute(server_summary_query)
        server_summary_rows = server_summary_result.all()

        # Get collection status (check latest collection time)
        latest_time_query = select(TrafficHistory).order_by(
            desc(TrafficHistory.timestamp)
        ).limit(1)
        latest_time_result = await db.execute(latest_time_query)
        latest_record = latest_time_result.scalar_one_or_none()

        collection_status = {
            "last_collection": latest_record.timestamp if latest_record else None,
            "collection_active": latest_record is not None,
            "collection_interval": "5 minutes"
        }

        # Calculate totals
        total_active_users = len(latest_rows)
        total_bandwidth_usage = sum(float(traffic.total_mbps) for traffic, _, _, _ in latest_rows)

        # Format top consumers
        top_consumers = []
        for traffic, data_teknis, server, pelanggan in latest_rows[:10]:
            top_consumers.append(TrafficDataResponse(
                id=traffic.id,
                data_teknis_id=traffic.data_teknis_id,
                username_pppoe=traffic.username_pppoe,
                ip_address=traffic.ip_address,
                rx_mbps=round(traffic.rx_mbps, 2),
                tx_mbps=round(traffic.tx_mbps, 2),
                total_mbps=round(traffic.total_mbps, 2),
                uptime_seconds=traffic.uptime_seconds,
                is_active=traffic.is_active,
                timestamp=traffic.timestamp,
                pelanggan_name=pelanggan.nama if pelanggan else None,
                server_name=server.name if server else None,
                olt=data_teknis.olt if data_teknis else None
            ))

        # Format server summaries
        server_summary = []
        for row in server_summary_rows:
            max_bandwidth = 100  # 100Mbps
            total_mbps = float(row.total_mbps) if row.total_mbps else 0
            load_percentage = min((total_mbps / max_bandwidth) * 100, 100)

            server_summary.append(TrafficSummaryResponse(
                server_id=row.server_id,
                server_name=row.server_name,
                active_users=row.active_users,
                avg_mbps=round(float(row.avg_mbps), 2) if row.avg_mbps else 0,
                max_mbps=round(float(row.max_mbps), 2) if row.max_mbps else 0,
                total_mbps=round(total_mbps, 2),
                load_percentage=round(load_percentage, 1)
            ))

        return DashboardSummaryResponse(
            total_active_users=total_active_users,
            total_bandwidth_usage=round(total_bandwidth_usage, 2),
            top_consumers=top_consumers,
            server_summary=server_summary,
            collection_status=collection_status,
            last_updated=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.post("/collect", response_model=CollectionResponse)
async def trigger_traffic_collection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Manual trigger untuk traffic collection.
    Runs in background task.
    """
    try:
        # Add background task for collection
        background_tasks.add_task(
            traffic_monitoring_service.collect_traffic_data,
            db
        )

        return CollectionResponse(
            status="success",
            message="Traffic collection started in background",
            data={
                "collection_interval": "5 minutes",
                "estimated_completion": "2-5 minutes"
            }
        )

    except Exception as e:
        logger.error(f"Error triggering traffic collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start traffic collection: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_traffic_statistics(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get traffic statistics untuk analisis.
    """
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get basic stats
        stats_query = select(
            func.count(TrafficHistory.id).label('total_records'),
            func.count(TrafficHistory.data_teknis_id.distinct()).label('unique_users'),
            func.avg(TrafficHistory.total_mbps).label('avg_bandwidth'),
            func.max(TrafficHistory.total_mbps).label('max_bandwidth'),
            func.sum(TrafficHistory.total_mbps).label('total_bandwidth')
        ).where(
            and_(
                TrafficHistory.is_latest == True,
                TrafficHistory.timestamp >= since
            )
        )

        stats_result = await db.execute(stats_query)
        stats = stats_result.first()

        # Get top OLTs by usage
        olt_query = select(
            DataTeknis.olt,
            func.count(TrafficHistory.id).label('user_count'),
            func.sum(TrafficHistory.total_mbps).label('total_bandwidth')
        ).join(
            TrafficHistory,
            DataTeknis.id == TrafficHistory.data_teknis_id
        ).where(
            and_(
                TrafficHistory.is_latest == True,
                TrafficHistory.timestamp >= since,
                DataTeknis.olt.isnot(None)
            )
        ).group_by(DataTeknis.olt).order_by(
            desc(func.sum(TrafficHistory.total_mbps))
        ).limit(10)

        olt_result = await db.execute(olt_query)
        top_olts = []

        for row in olt_result:
            top_olts.append({
                "olt": row.olt,
                "user_count": row.user_count,
                "total_bandwidth": round(float(row.total_bandwidth), 2)
            })

        return {
            "period_hours": hours,
            "total_records": stats.total_records if stats else 0,
            "unique_users": stats.unique_users if stats else 0,
            "avg_bandwidth_mbps": round(float(stats.avg_bandwidth), 2) if stats and stats.avg_bandwidth else 0,
            "max_bandwidth_mbps": round(float(stats.max_bandwidth), 2) if stats and stats.max_bandwidth else 0,
            "total_bandwidth_mbps": round(float(stats.total_bandwidth), 2) if stats and stats.total_bandwidth else 0,
            "top_olts": top_olts,
            "analysis_timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        logger.error(f"Error getting traffic statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get traffic statistics: {str(e)}"
        )