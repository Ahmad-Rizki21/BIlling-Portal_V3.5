# ====================================================================
# ANALYTICS ROUTER - AI ANALYTICS API ENDPOINTS
# ====================================================================
# Router ini menyediakan endpoint untuk AI-powered analytics.
# Terintegrasi dengan Z.AI (GLM-4) untuk analisis cerdas.
# ====================================================================

from __future__ import annotations
import logging
from datetime import date, datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_active_user
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.analytics import (
    # Requests
    RevenueAnalysisRequest,
    LatePaymentAnalysisRequest,
    CustomerBehaviorAnalysisRequest,
    ChatAnalyticsRequest,
    # Responses
    RevenueAnalysisResponse,
    LatePaymentAnalysisResponse,
    CustomerBehaviorAnalysisResponse,
    ChatAnalyticsResponse,
    RevenueDataResponse,
    LatePaymentDataResponse,
    CustomerBehaviorDataResponse,
)
from ..services.data_aggregation_service import DataAggregationService
from ..services.ai_analytics_service import AIAnalyticsService

logger = logging.getLogger("app.analytics")


# ====================================================================
# ROUTER SETUP
# ====================================================================

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    responses={
        401: {"detail": "Unauthorized"},
        403: {"detail": "Forbidden - Insufficient permissions"},
        429: {"detail": "Too many requests - Rate limit exceeded"}
    }
)

# ====================================================================
# RATE LIMITING (Simple in-memory implementation)
# ====================================================================

from collections import defaultdict
from time import time

# Simple rate limiter store: {user_id: [(timestamp1, timestamp2, ...)]}
_rate_limit_store: Dict[int, list] = defaultdict(list)


async def check_rate_limit(user_id: int, max_requests: int = None) -> bool:
    """
    Check if user has exceeded rate limit.

    Args:
        user_id: User ID
        max_requests: Maximum requests per minute (default from settings)

    Returns:
        bool: True if within limit, False if exceeded
    """
    if max_requests is None:
        max_requests = settings.ANALYTICS_RATE_LIMIT

    current_time = time()
    minute_ago = current_time - 60  # 60 seconds ago

    # Clean old timestamps
    _rate_limit_store[user_id] = [
        ts for ts in _rate_limit_store[user_id] if ts > minute_ago
    ]

    # Check if within limit
    if len(_rate_limit_store[user_id]) >= max_requests:
        return False

    # Add current request timestamp
    _rate_limit_store[user_id].append(current_time)
    return True


# ====================================================================
# ENDPOINTS - AI INSIGHTS
# ====================================================================

@router.post("/insights/revenue", response_model=RevenueAnalysisResponse)
async def get_revenue_insights(
    request: RevenueAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analisis pendapatan dengan AI.

    Mengambil data pendapatan dari periode yang ditentukan dan memberikan
    insight menggunakan Z.AI (GLM-4).

    Rate limit: 10 requests per minute per user.
    """
    # Check rate limit
    if not await check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maksimal {settings.ANALYTICS_RATE_LIMIT} requests per menit."
        )

    try:
        # Get aggregated data
        aggregation_service = DataAggregationService(db)
        revenue_data = await aggregation_service.get_revenue_data(
            start_date=request.start_date,
            end_date=request.end_date,
            brand=request.brand
        )

        # Get AI insights
        ai_service = AIAnalyticsService()
        insights = await ai_service.analyze_revenue(revenue_data)

        return RevenueAnalysisResponse(**insights)

    except Exception as e:
        logger.error(f"Error in revenue insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan insight: {str(e)}"
        )


@router.post("/insights/late-payments", response_model=LatePaymentAnalysisResponse)
async def get_late_payment_insights(
    request: LatePaymentAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analisis pembayaran telat dengan AI.

    Mengambil data pembayaran telat dan memberikan insight serta
    strategi follow-up menggunakan Z.AI.

    Rate limit: 10 requests per minute per user.
    """
    # Check rate limit
    if not await check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maksimal {settings.ANALYTICS_RATE_LIMIT} requests per menit."
        )

    try:
        # Get aggregated data
        aggregation_service = DataAggregationService(db)
        late_payment_data = await aggregation_service.get_late_payment_data(
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )

        # Get AI insights
        ai_service = AIAnalyticsService()
        insights = await ai_service.analyze_late_payments(late_payment_data)

        return LatePaymentAnalysisResponse(**insights)

    except Exception as e:
        logger.error(f"Error in late payment insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan insight: {str(e)}"
        )


@router.post("/insights/customer-behavior", response_model=CustomerBehaviorAnalysisResponse)
async def get_customer_behavior_insights(
    request: CustomerBehaviorAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analisis perilaku customer dengan AI.

    Mengambil data perilaku customer dan memberikan insight tentang
    segmentasi, CLV, churn risk, dan strategi retensi.

    Rate limit: 10 requests per minute per user.
    """
    # Check rate limit
    if not await check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maksimal {settings.ANALYTICS_RATE_LIMIT} requests per menit."
        )

    try:
        # Get aggregated data
        aggregation_service = DataAggregationService(db)
        customer_data = await aggregation_service.get_customer_behavior_metrics(
            limit=request.limit
        )

        # Get AI insights
        ai_service = AIAnalyticsService()
        insights = await ai_service.analyze_customer_behavior(customer_data)

        return CustomerBehaviorAnalysisResponse(**insights)

    except Exception as e:
        logger.error(f"Error in customer behavior insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan insight: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - RAW DATA (Tanpa AI)
# ====================================================================

@router.get("/data/revenue", response_model=RevenueDataResponse)
async def get_revenue_data(
    start_date: date,
    end_date: date,
    brand: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ambil data pendapatan mentah (tanpa AI analysis).

    Berguna untuk chart dan visualisasi di frontend.
    """
    try:
        aggregation_service = DataAggregationService(db)
        data = await aggregation_service.get_revenue_data(
            start_date=start_date,
            end_date=end_date,
            brand=brand
        )
        return RevenueDataResponse(**data)

    except Exception as e:
        logger.error(f"Error getting revenue data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data: {str(e)}"
        )


@router.get("/data/late-payments", response_model=LatePaymentDataResponse)
async def get_late_payment_data(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ambil data pembayaran telat mentah (tanpa AI analysis).

    Berguna untuk tabel dan visualisasi di frontend.
    """
    try:
        aggregation_service = DataAggregationService(db)
        data = await aggregation_service.get_late_payment_data(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return LatePaymentDataResponse(**data)

    except Exception as e:
        logger.error(f"Error getting late payment data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data: {str(e)}"
        )


@router.get("/data/customer-behavior", response_model=CustomerBehaviorDataResponse)
async def get_customer_behavior_data(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ambil data perilaku customer mentah (tanpa AI analysis).

    Berguna untuk chart dan visualisasi di frontend.
    """
    try:
        aggregation_service = DataAggregationService(db)
        data = await aggregation_service.get_customer_behavior_metrics(limit=limit)
        return CustomerBehaviorDataResponse(**data)

    except Exception as e:
        logger.error(f"Error getting customer behavior data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - CHAT INTERFACE
# ====================================================================

@router.post("/chat", response_model=ChatAnalyticsResponse)
async def chat_analytics(
    request: ChatAnalyticsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat interface untuk analytics.

    User bisa bertanya tentang data analytics dalam natural language
    dan mendapatkan jawaban dari AI.

    Contoh pertanyaan:
    - "Bagaimana tren pendapatan bulan ini?"
    - "Berapa jumlah pelanggan sekarang?"
    - "Customer mana yang paling berisiko churn?"
    - "Berapa total outstanding dari pembayaran telat?"

    Context akan otomatis dideteksi dari pertanyaan jika tidak ditentukan.
    """
    # Check rate limit
    if not await check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maksimal {settings.ANALYTICS_RATE_LIMIT} requests per menit."
        )

    try:
        ai_service = AIAnalyticsService()
        aggregation_service = DataAggregationService(db)

        # Auto-detect context from question if not specified
        context_type = request.context_type
        context_data = None

        # Keywords untuk auto-detect context
        question_lower = request.question.lower()
        logger.info(f"Chat question: {request.question}")
        logger.info(f"Request context_type: {request.context_type}")

        if not context_type:
            # Auto-detect based on keywords
            revenue_keywords = ["pendapatan", "revenue", "income", "uang", "pemasukan", "invoice", "tagihan"]
            customer_keywords = ["pelanggan", "customer", "user", "jumlah user", "berapa user", "banyak user", "total pelanggan"]
            late_payment_keywords = ["telat", "late", "tunggakan", "outstanding", "belum bayar", "jatuh tempo"]

            if any(kw in question_lower for kw in revenue_keywords):
                context_type = "revenue"
            elif any(kw in question_lower for kw in customer_keywords):
                context_type = "customer_behavior"
            elif any(kw in question_lower for kw in late_payment_keywords):
                context_type = "late_payments"

            logger.info(f"Auto-detected context_type: {context_type}")

        # Fetch context data based on detected/specified type
        if context_type == "revenue":
            # Default: last 30 days
            end = date.today()
            start = date.fromordinal(end.toordinal() - 30)
            context_data = await aggregation_service.get_revenue_data(start, end)

        elif context_type == "late_payments":
            context_data = await aggregation_service.get_late_payment_data(limit=50)

        elif context_type == "customer_behavior":
            context_data = await aggregation_service.get_customer_behavior_metrics(limit=100)
            # Log the data to verify total_customers is present
            if context_data and "total_customers" in context_data:
                logger.info(f"Customer data loaded. total_customers: {context_data['total_customers']}")
            else:
                logger.warning("Customer data loaded but total_customers field is missing!")

        # Log what data is being sent to AI
        if context_data:
            logger.info(f"Sending context to AI. Keys: {list(context_data.keys())}")
        else:
            logger.info("No context data sent to AI")

        # Get AI response
        answer = await ai_service.chat_analytics(request.question, context_data)

        return ChatAnalyticsResponse(
            answer=answer,
            context_used=context_type or "none"
        )

    except Exception as e:
        logger.error(f"Error in chat analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses pertanyaan: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - DASHBOARD SUMMARY
# ====================================================================

@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ambil ringkasan analytics untuk dashboard.

    Memberikan snapshot data penting tanpa memanggil AI.
    """
    try:
        aggregation_service = DataAggregationService(db)

        # Get recent revenue data (last 30 days)
        end = date.today()
        start = date.fromordinal(end.toordinal() - 30)
        revenue_data = await aggregation_service.get_revenue_data(start, end)

        # Get late payment summary
        late_payment_data = await aggregation_service.get_late_payment_data(limit=20)

        # Get customer behavior summary
        customer_data = await aggregation_service.get_customer_behavior_metrics(limit=50)

        return {
            "revenue": {
                "total_revenue": revenue_data["total_revenue"],
                "paid_revenue": revenue_data["paid_revenue"],
                "collection_rate": revenue_data["collection_rate"],
                "growth_rate": revenue_data["growth_rate"],
                "forecast_next_month": revenue_data["forecast_next_month"]
            },
            "late_payments": {
                "total_late_customers": late_payment_data["total_late_customers"],
                "total_outstanding": late_payment_data["total_outstanding"],
                "avg_days_late": late_payment_data["avg_days_late"],
                "high_risk_count": late_payment_data["risk_segments"]["high_risk"]
            },
            "customers": {
                "total_customers": customer_data["total_customers_analyzed"],
                "avg_loyalty_score": customer_data["loyalty_analysis"]["avg_loyalty_score"],
                "avg_churn_risk": customer_data["churn_risk_analysis"]["avg_churn_risk"],
                "high_churn_risk_count": customer_data["churn_risk_analysis"]["high_risk_count"]
            },
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan ringkasan: {str(e)}"
        )
