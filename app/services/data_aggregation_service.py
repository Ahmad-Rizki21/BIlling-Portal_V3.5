# ====================================================================
# DATA AGGREGATION SERVICE - AI ANALYTICS
# ====================================================================
# Service ini mengambil dan mengagregasi data dari database untuk
# dianalisis oleh AI. Data yang dikirim ke AI sudah dalam bentuk
# aggregated dan sanitized (PII di-mask).
# ====================================================================

from __future__ import annotations
import hashlib
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.invoice import Invoice
from ..models.pelanggan import Pelanggan
from ..models.langganan import Langganan


# ====================================================================
# PII SANITIZATION - DATA PRIVACY PROTECTION
# ====================================================================

def mask_email(email: str | None) -> str:
    """Mask email address untuk privacy."""
    if not email:
        return "unknown@example.com"
    parts = email.split("@")
    if len(parts) != 2:
        return "unknown@example.com"
    username, domain = parts
    if len(username) <= 2:
        masked_username = "***"
    else:
        masked_username = username[:2] + "***"
    return f"{masked_username}@{domain}"


def mask_phone(phone: str | None) -> str:
    """Mask nomor telepon untuk privacy."""
    if not phone:
        return "+628******0000"
    # Tampilkan 4 digit pertama dan terakhir saja
    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")
    if len(phone_clean) <= 4:
        return "+628******0000"
    return f"+62{phone_clean[1:4]}******{phone_clean[-2:]}"


def mask_address(address: str | None) -> str:
    """Mask alamat untuk privacy - hanya tampilkan kota/region."""
    if not address:
        return "Indonesia"
    # Ambil region dari alamat (kota, kabupaten, dll)
    words = address.split()
    # Cari kata-kata khas Indonesia (Kota, Kab, Kec, Desa, dll)
    region_keywords = ["Kota", "Kab", "Kec", "Desa", "Kel", "Jawa", "Sumatera", "Kalimantan", "Sulawesi", "Papua", "Bali", "Nusa"]
    for i, word in enumerate(words):
        for keyword in region_keywords:
            if keyword in word:
                # Ambil dari kata ini dan 2 kata berikutnya
                region = " ".join(words[i:i+3])
                return region[:50]  # Max 50 karakter
    # Default: ambil 3 kata terakhir sebagai region
    return " ".join(words[-3:])[:50] if len(words) > 3 else "Indonesia"


def mask_nama(nama: str | None) -> str:
    """Mask nama untuk privacy."""
    if not nama:
        return "Pelanggan XXX"
    words = nama.split()
    if len(words) == 0:
        return "Pelanggan XXX"
    # Tampilkan nama depan (max 2 karakter) dan XXX untuk sisanya
    first_word = words[0]
    if len(first_word) <= 2:
        masked_first = "**"
    else:
        masked_first = first_word[:2] + "**"
    # Untuk nama yang hanya 1 kata
    if len(words) == 1:
        return f"Pelanggan {masked_first}"
    # Untuk nama dengan > 1 kata, tampilkan kata terakhir yang di-mask
    last_word = words[-1]
    if len(last_word) <= 2:
        masked_last = "**"
    else:
        masked_last = last_word[:2] + "**"
    return f"{masked_first} {masked_last}"


# ====================================================================
# DATA AGGREGATION SERVICE
# ====================================================================

class DataAggregationService:
    """
    Service untuk mengambil dan mengagregasi data untuk AI Analytics.
    Semua data PII di-mask sebelum dikirim ke AI.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # --------------------------------------------------------------------
    # REVENUE DATA AGGREGATION
    # --------------------------------------------------------------------

    async def get_revenue_data(
        self,
        start_date: date,
        end_date: date,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mengambil dan mengagregasi data pendapatan untuk analisis AI.

        Returns:
            Dict berisi:
            - total_revenue: Total pendapatan dalam periode
            - paid_revenue: Pendapatan dari invoice yang sudah lunas
            - pending_revenue: Pendapatan dari invoice yang belum lunas
            - daily_revenue: Array pendapatan harian
            - monthly_revenue: Array pendapatan bulanan
            - payment_methods: Distribusi metode pembayaran
            - revenue_by_brand: Pendapatan per brand
            - growth_rate: Tingkat pertumbuhan vs periode sebelumnya
            - forecast: Prediksi pendapatan bulan depan
        """
        # Base query untuk revenue
        query = (
            select(Invoice)
            .where(
                and_(
                    Invoice.tgl_invoice >= start_date,
                    Invoice.tgl_invoice <= end_date,
                    Invoice.deleted_at.is_(None)
                )
            )
        )

        # Filter by brand jika specified
        if brand:
            query = query.where(Invoice.brand == brand)

        # Execute query
        result = await self.db.execute(query)
        invoices = result.scalars().all()

        # Aggregate data
        total_revenue = sum(inv.total_harga or 0 for inv in invoices)
        paid_revenue = sum(inv.paid_amount or 0 for inv in invoices if inv.status_invoice == "Lunas")
        pending_revenue = total_revenue - paid_revenue

        # Daily revenue
        daily_revenue = {}
        for inv in invoices:
            inv_date = str(inv.tgl_invoice)
            if inv_date not in daily_revenue:
                daily_revenue[inv_date] = {"total": 0, "paid": 0, "pending": 0}
            daily_revenue[inv_date]["total"] += inv.total_harga or 0
            if inv.status_invoice == "Lunas":
                daily_revenue[inv_date]["paid"] += inv.paid_amount or 0
            else:
                daily_revenue[inv_date]["pending"] += inv.total_harga or 0

        # Convert daily_revenue ke list
        daily_revenue_list = [
            {
                "date": d,
                "total": float(v["total"]),
                "paid": float(v["paid"]),
                "pending": float(v["pending"])
            }
            for d, v in sorted(daily_revenue.items())
        ]

        # Monthly revenue
        monthly_revenue = {}
        for inv in invoices:
            month_key = inv.tgl_invoice.strftime("%Y-%m")
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = {"total": 0, "count": 0}
            monthly_revenue[month_key]["total"] += inv.total_harga or 0
            monthly_revenue[month_key]["count"] += 1

        monthly_revenue_list = [
            {
                "month": m,
                "total": float(v["total"]),
                "count": v["count"]
            }
            for m, v in sorted(monthly_revenue.items())
        ]

        # Payment methods distribution
        payment_methods = {}
        for inv in invoices:
            method = inv.metode_pembayaran or "Unknown"
            if method not in payment_methods:
                payment_methods[method] = {"count": 0, "amount": 0}
            payment_methods[method]["count"] += 1
            if inv.paid_amount:
                payment_methods[method]["amount"] += inv.paid_amount

        payment_methods_list = [
            {
                "method": m,
                "count": v["count"],
                "amount": float(v["amount"])
            }
            for m, v in sorted(payment_methods.items(), key=lambda x: x[1]["amount"], reverse=True)
        ]

        # Revenue by brand
        revenue_by_brand = {}
        for inv in invoices:
            b = inv.brand or "Unknown"
            if b not in revenue_by_brand:
                revenue_by_brand[b] = {"total": 0, "paid": 0, "count": 0}
            revenue_by_brand[b]["total"] += inv.total_harga or 0
            revenue_by_brand[b]["count"] += 1
            if inv.status_invoice == "Lunas":
                revenue_by_brand[b]["paid"] += inv.paid_amount or 0

        revenue_by_brand_list = [
            {
                "brand": b,
                "total": float(v["total"]),
                "paid": float(v["paid"]),
                "count": v["count"],
                "collection_rate": float(v["paid"] / v["total"] * 100) if v["total"] > 0 else 0
            }
            for b, v in sorted(revenue_by_brand.items(), key=lambda x: x[1]["total"], reverse=True)
        ]

        # Calculate growth rate vs previous period
        previous_start = start_date - timedelta(days=(end_date - start_date).days + 1)
        previous_end = start_date - timedelta(days=1)

        prev_query = (
            select(func.sum(Invoice.total_harga))
            .where(
                and_(
                    Invoice.tgl_invoice >= previous_start,
                    Invoice.tgl_invoice <= previous_end,
                    Invoice.status_invoice == "Lunas",
                    Invoice.deleted_at.is_(None)
                )
            )
        )
        if brand:
            prev_query = prev_query.where(Invoice.brand == brand)

        prev_result = await self.db.execute(prev_query)
        previous_revenue = prev_result.scalar() or 0

        growth_rate = 0.0
        if previous_revenue > 0:
            growth_rate = float((paid_revenue - previous_revenue) / previous_revenue * 100)

        # Simple forecast (linear trend)
        if len(monthly_revenue_list) >= 2:
            # Hitung rata-rata growth per bulan
            monthly_values = [m["total"] for m in monthly_revenue_list]
            avg_monthly_growth = (monthly_values[-1] - monthly_values[0]) / len(monthly_values)
            forecast_next_month = float(monthly_values[-1] + avg_monthly_growth)
        else:
            forecast_next_month = float(paid_revenue)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "total_revenue": float(total_revenue),
            "paid_revenue": float(paid_revenue),
            "pending_revenue": float(pending_revenue),
            "collection_rate": float(paid_revenue / total_revenue * 100) if total_revenue > 0 else 0,
            "daily_revenue": daily_revenue_list,
            "monthly_revenue": monthly_revenue_list,
            "payment_methods": payment_methods_list,
            "revenue_by_brand": revenue_by_brand_list,
            "growth_rate": growth_rate,
            "previous_period_revenue": float(previous_revenue),
            "forecast_next_month": forecast_next_month,
            "total_invoices": len(invoices),
            "paid_invoices": sum(1 for inv in invoices if inv.status_invoice == "Lunas"),
            "pending_invoices": sum(1 for inv in invoices if inv.status_invoice != "Lunas")
        }

    # --------------------------------------------------------------------
    # LATE PAYMENT DATA AGGREGATION
    # --------------------------------------------------------------------

    async def get_late_payment_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Mengambil data pembayaran telat untuk analisis AI.

        Returns:
            Dict berisi:
            - late_customers: Daftar customer dengan pembayaran telat (PII masked)
            - late_payment_stats: Statistik pembayaran telat
            - risk_segments: Segmentasi customer berdasarkan risiko
            - follow_up_suggestions: Saran follow-up
        """
        today = date.today()

        # Default: 3 months back
        if not start_date:
            start_date = today - timedelta(days=90)
        if not end_date:
            end_date = today

        # Query untuk invoice yang telat bayar
        query = (
            select(Invoice)
            .options(selectinload(Invoice.pelanggan))
            .where(
                and_(
                    Invoice.tgl_jatuh_tempo < today,
                    Invoice.status_invoice.in_(["Belum Dibayar", "Expired"]),
                    Invoice.deleted_at.is_(None),
                    Invoice.tgl_invoice >= start_date,
                    Invoice.tgl_invoice <= end_date
                )
            )
            .order_by(Invoice.tgl_jatuh_tempo)
            .limit(limit)
        )

        result = await self.db.execute(query)
        late_invoices = result.scalars().all()

        # Aggregate data per customer
        late_customers = {}
        for inv in late_invoices:
            customer_id = inv.pelanggan_id
            if customer_id not in late_customers:
                # Mask PII data
                customer = inv.pelanggan
                late_customers[customer_id] = {
                    "customer_id": customer_id,
                    "nama": mask_nama(customer.nama if customer else None),
                    "brand": inv.brand,
                    "no_telp": mask_phone(inv.no_telp),
                    "email": mask_email(inv.email),
                    "alamat": mask_address(customer.alamat if customer else None),
                    "late_invoices": [],
                    "total_outstanding": 0,
                    "days_late_avg": 0,
                    "risk_score": 0
                }

            # Calculate days late
            days_late = (today - inv.tgl_jatuh_tempo).days
            late_customers[customer_id]["late_invoices"].append({
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.tgl_invoice.isoformat(),
                "due_date": inv.tgl_jatuh_tempo.isoformat(),
                "amount": float(inv.total_harga),
                "days_late": days_late,
                "status": inv.status_invoice,
                "brand": inv.brand
            })
            late_customers[customer_id]["total_outstanding"] += float(inv.total_harga)

        # Calculate risk score and average days late
        for customer_id, data in late_customers.items():
            invoice_count = len(data["late_invoices"])
            if invoice_count > 0:
                data["days_late_avg"] = sum(inv["days_late"] for inv in data["late_invoices"]) / invoice_count

            # Risk score calculation (0-100)
            # Factors: total outstanding, days late avg, invoice count
            outstanding_score = min(data["total_outstanding"] / 1000000 * 30, 30)  # Max 30 poin
            days_score = min(data["days_late_avg"] / 30 * 40, 40)  # Max 40 poin
            count_score = min(invoice_count * 10, 30)  # Max 30 poin
            data["risk_score"] = int(outstanding_score + days_score + count_score)

        # Convert to list and sort by risk score
        late_customers_list = sorted(
            late_customers.values(),
            key=lambda x: x["risk_score"],
            reverse=True
        )

        # Calculate statistics
        total_outstanding = sum(c["total_outstanding"] for c in late_customers_list)
        avg_days_late = sum(c["days_late_avg"] for c in late_customers_list) / len(late_customers_list) if late_customers_list else 0

        # Risk segmentation
        risk_segments = {
            "high_risk": [c for c in late_customers_list if c["risk_score"] >= 70],
            "medium_risk": [c for c in late_customers_list if 50 <= c["risk_score"] < 70],
            "low_risk": [c for c in late_customers_list if c["risk_score"] < 50]
        }

        # Follow-up suggestions
        follow_up_suggestions = []
        for customer in late_customers_list[:10]:  # Top 10 highest risk
            if customer["risk_score"] >= 70:
                follow_up_suggestions.append({
                    "priority": "HIGH",
                    "customer": customer["nama"],
                    "no_telp": customer["no_telp"],
                    "action": "Immediate follow-up required",
                    "reason": f"Risk score: {customer['risk_score']}, Outstanding: Rp {customer['total_outstanding']:,.0f}"
                })
            elif customer["risk_score"] >= 50:
                follow_up_suggestions.append({
                    "priority": "MEDIUM",
                    "customer": customer["nama"],
                    "no_telp": customer["no_telp"],
                    "action": "Schedule follow-up call",
                    "reason": f"Risk score: {customer['risk_score']}, Days late avg: {customer['days_late_avg']:.0f}"
                })

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_late_customers": len(late_customers_list),
            "total_outstanding": float(total_outstanding),
            "avg_days_late": float(avg_days_late),
            "late_customers": late_customers_list[:50],  # Limit to 50 for AI
            "risk_segments": {
                "high_risk": len(risk_segments["high_risk"]),
                "medium_risk": len(risk_segments["medium_risk"]),
                "low_risk": len(risk_segments["low_risk"])
            },
            "follow_up_suggestions": follow_up_suggestions[:10]
        }

    # --------------------------------------------------------------------
    # CUSTOMER BEHAVIOR DATA AGGREGATION
    # --------------------------------------------------------------------

    async def get_customer_behavior_metrics(
        self,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Mengambil metrics behavior customer untuk analisis AI.

        Returns:
            Dict berisi:
            - total_customers: Total semua customer di database
            - customer_segments: Segmentasi customer berdasarkan behavior
            - payment_patterns: Pola pembayaran customer
            - clv_analysis: Customer Lifetime Value analysis
            - churn_risk: Prediksi risiko churn
        """
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        # Get TOTAL customers first (untuk menjawab pertanyaan "berapa jumlah customer")
        # Catatan: Model Pelanggan tidak punya deleted_at, jadi hitung semua
        total_customers_query = select(func.count(Pelanggan.id))
        total_result = await self.db.execute(total_customers_query)
        total_all_customers = total_result.scalar() or 0

        # Get customer data with payment history (hanya yang punya invoice)
        query = (
            select(Pelanggan)
            .join(Invoice, Invoice.pelanggan_id == Pelanggan.id)
            .where(
                and_(
                    Invoice.tgl_invoice >= six_months_ago,
                    Invoice.deleted_at.is_(None)
                )
            )
            .distinct()
            .limit(limit)
        )

        result = await self.db.execute(query)
        customers = result.scalars().all()

        # Analyze each customer
        customer_metrics = []
        for customer in customers:
            # Get invoices for this customer
            inv_query = (
                select(Invoice)
                .where(
                    and_(
                        Invoice.pelanggan_id == customer.id,
                        Invoice.tgl_invoice >= six_months_ago,
                        Invoice.deleted_at.is_(None)
                    )
                )
                .order_by(Invoice.tgl_invoice.desc())
            )
            inv_result = await self.db.execute(inv_query)
            invoices = inv_result.scalars().all()

            if not invoices:
                continue

            # Calculate metrics
            total_invoices = len(invoices)
            paid_invoices = sum(1 for inv in invoices if inv.status_invoice == "Lunas")
            total_spent = float(sum(inv.paid_amount or 0 for inv in invoices if inv.status_invoice == "Lunas"))

            # Calculate average payment days (how fast they pay)
            payment_days = []
            for inv in invoices:
                if inv.paid_at and inv.tgl_invoice:
                    paid_date = inv.paid_at.date() if isinstance(inv.paid_at, datetime) else inv.paid_at
                    inv_date = inv.tgl_invoice
                    days_to_pay = (paid_date - inv_date).days
                    payment_days.append(days_to_pay)

            avg_payment_days = sum(payment_days) / len(payment_days) if payment_days else 0

            # Late payment rate
            late_payments = sum(1 for inv in invoices if inv.tgl_jatuh_tempo and inv.paid_at and inv.paid_at.date() > inv.tgl_jatuh_tempo)
            late_payment_rate = (late_payments / total_invoices * 100) if total_invoices > 0 else 0

            # Calculate CLV (simplified: monthly avg * 12 months)
            months_active = max(1, (today - customer.created_at.date()).days / 30 if customer.created_at else 1)
            avg_monthly_spend = float(total_spent) / months_active if months_active > 0 else 0
            estimated_clv = avg_monthly_spend * 12

            # Calculate loyalty score (0-100)
            on_time_payment_rate = 100 - late_payment_rate
            loyalty_score = int((on_time_payment_rate * 0.6) + (min(total_invoices, 12) / 12 * 20) + (min(months_active, 36) / 36 * 20))

            # Churn risk (inverse of loyalty score)
            churn_risk = max(0, min(100, 100 - loyalty_score + int(late_payment_rate * 0.5)))

            # Segment customer
            if estimated_clv > 5000000 and loyalty_score >= 70:
                segment = "VIP - High Value"
            elif estimated_clv > 2000000:
                segment = "Premium"
            elif loyalty_score >= 70:
                segment = "Loyal"
            elif late_payment_rate > 50:
                segment = "At Risk"
            else:
                segment = "Regular"

            customer_metrics.append({
                "customer_id": customer.id,
                "nama": customer.nama,  # Tidak di-mask untuk ditampilkan lengkap
                "brand": customer.id_brand,
                "segment": segment,
                "total_invoices": total_invoices,
                "paid_invoices": paid_invoices,
                "payment_rate": float(paid_invoices / total_invoices * 100) if total_invoices > 0 else 0,
                "total_spent": float(total_spent),
                "avg_monthly_spend": float(avg_monthly_spend),
                "estimated_clv": float(estimated_clv),
                "avg_payment_days": float(avg_payment_days),
                "late_payment_rate": float(late_payment_rate),
                "loyalty_score": loyalty_score,
                "churn_risk": churn_risk,
                "months_active": float(months_active)
            })

        # Segment analysis
        segments = {}
        for cm in customer_metrics:
            seg = cm["segment"]
            if seg not in segments:
                segments[seg] = {"count": 0, "total_clv": 0, "avg_loyalty": 0}
            segments[seg]["count"] += 1
            segments[seg]["total_clv"] += cm["estimated_clv"]

        segment_analysis = [
            {
                "segment": seg,
                "count": data["count"],
                "total_clv": float(data["total_clv"]),
                "avg_clv": float(data["total_clv"] / data["count"]) if data["count"] > 0 else 0
            }
            for seg, data in sorted(segments.items(), key=lambda x: x[1]["total_clv"], reverse=True)
        ]

        # Churn risk analysis
        high_churn_risk = [cm for cm in customer_metrics if cm["churn_risk"] >= 60]
        medium_churn_risk = [cm for cm in customer_metrics if 40 <= cm["churn_risk"] < 60]

        return {
            "period": {
                "start": six_months_ago.isoformat(),
                "end": today.isoformat()
            },
            "total_customers": total_all_customers,  # Total SEMUA customer di database
            "total_customers_analyzed": len(customer_metrics),  # Customer yang dianalisis (punya invoice)
            "customers_with_recent_activity": len(customer_metrics),  # Customer dengan invoice 6 bulan terakhir
            "customer_segments": segment_analysis,
            "top_customers": sorted(customer_metrics, key=lambda x: x["estimated_clv"], reverse=True)[:20],
            "churn_risk_analysis": {
                "high_risk_count": len(high_churn_risk),
                "medium_risk_count": len(medium_churn_risk),
                "high_risk_customers": high_churn_risk[:10],  # Top 10 highest risk
                "avg_churn_risk": float(sum(cm["churn_risk"] for cm in customer_metrics) / len(customer_metrics)) if customer_metrics else 0
            },
            "loyalty_analysis": {
                "avg_loyalty_score": float(sum(cm["loyalty_score"] for cm in customer_metrics) / len(customer_metrics)) if customer_metrics else 0,
                "loyal_customers": sum(1 for cm in customer_metrics if cm["loyalty_score"] >= 70)
            },
            "payment_patterns": {
                "avg_payment_days": float(sum(cm["avg_payment_days"] for cm in customer_metrics) / len(customer_metrics)) if customer_metrics else 0,
                "avg_late_payment_rate": float(sum(cm["late_payment_rate"] for cm in customer_metrics) / len(customer_metrics)) if customer_metrics else 0
            }
        }
