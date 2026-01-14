# ====================================================================
# PYDANTIC SCHEMAS - AI ANALYTICS API
# ====================================================================
# Schemas untuk validasi request dan response AI Analytics API.
# ====================================================================

from __future__ import annotations
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ====================================================================
# REQUEST SCHEMAS
# ====================================================================

class AnalyticsQueryBase(BaseModel):
    """Base schema untuk analytics query."""

    query_type: str = Field(
        ...,
        description="Jenis analisis: revenue, late_payments, customer_behavior",
        pattern="^(revenue|late_payments|customer_behavior)$"
    )


class RevenueAnalysisRequest(AnalyticsQueryBase):
    """Request untuk analisis pendapatan."""

    query_type: str = Field(default="revenue", description="Tipe query: revenue")
    start_date: date = Field(..., description="Tanggal awal periode")
    end_date: date = Field(..., description="Tanggal akhir periode")
    brand: Optional[str] = Field(None, description="Filter berdasarkan brand")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date harus lebih besar atau sama dengan start_date')
        return v


class LatePaymentAnalysisRequest(AnalyticsQueryBase):
    """Request untuk analisis pembayaran telat."""

    query_type: str = Field(default="late_payments", description="Tipe query: late_payments")
    start_date: Optional[date] = Field(None, description="Tanggal awal (default: 3 bulan ke belakang)")
    end_date: Optional[date] = Field(None, description="Tanggal akhir (default: hari ini)")
    limit: int = Field(default=100, ge=1, le=500, description="Maksimal jumlah customer")


class CustomerBehaviorAnalysisRequest(AnalyticsQueryBase):
    """Request untuk analisis perilaku customer."""

    query_type: str = Field(default="customer_behavior", description="Tipe query: customer_behavior")
    limit: int = Field(default=100, ge=1, le=500, description="Maksimal jumlah customer")


class ChatAnalyticsRequest(BaseModel):
    """Request untuk chat analytics."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Pertanyaan dari user"
    )
    context_type: Optional[str] = Field(
        None,
        description="Tipe konteks: revenue, late_payments, customer_behavior",
        pattern="^(revenue|late_payments|customer_behavior)$"
    )
    context_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameter tambahan untuk konteks"
    )


# ====================================================================
# RESPONSE SCHEMAS
# ====================================================================

class AIInsightResponse(BaseModel):
    """Response standar untuk AI insight."""

    summary: str = Field(..., description="Ringkasan analisis")
    data_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Snapshot data yang dianalisis")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")


class RevenueAnalysisResponse(AIInsightResponse):
    """Response untuk analisis pendapatan."""

    key_findings: List[str] = Field(default_factory=list, description="Temuan penting")
    recommendations: List[str] = Field(default_factory=list, description="Rekomendasi")
    opportunities: List[str] = Field(default_factory=list, description="Peluang bisnis")
    risks: List[str] = Field(default_factory=list, description="Risiko yang perlu diwaspadai")


class LatePaymentAnalysisResponse(AIInsightResponse):
    """Response untuk analisis pembayaran telat."""

    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Penilaian risiko")
    follow_up_strategy: List[str] = Field(default_factory=list, description="Strategi follow-up")
    prevention_recommendations: List[str] = Field(default_factory=list, description="Rekomendasi pencegahan")
    communication_template: Optional[Dict[str, str]] = Field(None, description="Template pesan follow-up")


class CustomerBehaviorAnalysisResponse(AIInsightResponse):
    """Response untuk analisis perilaku customer."""

    customer_insights: Dict[str, Any] = Field(default_factory=dict, description="Insight customer")
    segment_analysis: List[Dict[str, Any]] = Field(default_factory=list, description="Analisis segment")
    retention_strategies: List[str] = Field(default_factory=list, description="Strategi retensi")
    upsell_opportunities: List[str] = Field(default_factory=list, description="Peluang upsell")


class ChatAnalyticsResponse(BaseModel):
    """Response untuk chat analytics."""

    answer: str = Field(..., description="Jawaban dari AI")
    context_used: Optional[str] = Field(None, description="Konteks yang digunakan (jika ada)")


# ====================================================================
# DATA RESPONSE SCHEMAS
# ====================================================================

class RevenueDataResponse(BaseModel):
    """Response untuk data pendapatan (tanpa AI analysis)."""

    period: Dict[str, Any]
    total_revenue: float
    paid_revenue: float
    pending_revenue: float
    collection_rate: float
    daily_revenue: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]
    payment_methods: List[Dict[str, Any]]
    revenue_by_brand: List[Dict[str, Any]]
    growth_rate: float
    forecast_next_month: float
    total_invoices: int
    paid_invoices: int
    pending_invoices: int


class LatePaymentDataResponse(BaseModel):
    """Response untuk data pembayaran telat (tanpa AI analysis)."""

    period: Dict[str, Any]
    total_late_customers: int
    total_outstanding: float
    avg_days_late: float
    late_customers: List[Dict[str, Any]]
    risk_segments: Dict[str, int]
    follow_up_suggestions: List[Dict[str, Any]]


class CustomerBehaviorDataResponse(BaseModel):
    """Response untuk data perilaku customer (tanpa AI analysis)."""

    period: Dict[str, Any]
    total_customers_analyzed: int
    customer_segments: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]
    churn_risk_analysis: Dict[str, Any]
    loyalty_analysis: Dict[str, Any]
    payment_patterns: Dict[str, Any]


# ====================================================================
# EXPORT SCHEMAS
# ====================================================================

class ExportInsightsRequest(BaseModel):
    """Request untuk export insights."""

    insight_type: str = Field(..., pattern="^(revenue|late_payments|customer_behavior)$")
    format: str = Field(default="pdf", pattern="^(pdf|excel)$")
    data: Dict[str, Any] = Field(..., description="Data yang akan di-export")


class ExportInsightsResponse(BaseModel):
    """Response untuk export insights."""

    status: str = Field(..., description="Status: success, failed")
    message: str = Field(..., description="Pesan status")
    download_url: Optional[str] = Field(None, description="URL untuk download file")
