#!/usr/bin/env python3
"""
Query Optimization Utilities for Eliminating N+1 Problems
"""

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.models.data_teknis import DataTeknis
from app.models.invoice import Invoice
from app.models.langganan import Langganan
from app.models.pelanggan import Pelanggan


def optimize_pelanggan_query_with_stats(query):
    """
    Optimasi query pelanggan dengan statistik agregat untuk menghindari N+1 problem
    """
    # Tambahkan subquery untuk menghitung jumlah invoice per pelanggan
    invoice_count_subq = (
        select(
            Invoice.pelanggan_id,
            func.count(Invoice.id).label("invoice_count"),
            func.sum(Invoice.total_harga).label("total_invoice_amount"),
        )
        .group_by(Invoice.pelanggan_id)
        .subquery()
    )

    # Tambahkan subquery untuk menghitung jumlah langganan per pelanggan
    langganan_count_subq = (
        select(Langganan.pelanggan_id, func.count(Langganan.id).label("langganan_count"))
        .group_by(Langganan.pelanggan_id)
        .subquery()
    )

    # Gabungkan query utama dengan subquery statistik
    optimized_query = query.outerjoin(invoice_count_subq, Pelanggan.id == invoice_count_subq.c.pelanggan_id).outerjoin(
        langganan_count_subq, Pelanggan.id == langganan_count_subq.c.pelanggan_id
    )

    return optimized_query


def optimize_invoice_query_with_related(query):
    """
    Optimasi query invoice dengan relasi yang sering digunakan bersama
    """
    # Gunakan joinedload untuk relasi yang selalu dibutuhkan
    optimized_query = query.options(
        joinedload(Invoice.pelanggan).joinedload(Pelanggan.harga_layanan),
        joinedload(Invoice.pelanggan).joinedload(Pelanggan.langganan).joinedload(Langganan.paket_layanan),
        joinedload(Invoice.pelanggan).joinedload(Pelanggan.data_teknis),
    )

    return optimized_query


def add_pagination_optimization(query, skip=0, limit=100):
    """
    Tambahkan optimasi pagination yang efisien
    """
    # Gunakan keyset pagination untuk query yang lebih efisien daripada OFFSET
    # Tapi untuk sekarang kita tetap gunakan LIMIT/OFFSET dengan optimasi
    optimized_query = query.offset(skip).limit(limit)
    return optimized_query


def get_pelanggan_with_aggregate_stats(db, skip=0, limit=100):
    """
    Query pelanggan dengan statistik agregat untuk menghindari N+1 problem
    """
    # Subquery untuk menghitung statistik
    invoice_stats = (
        select(
            Invoice.pelanggan_id,
            func.count(Invoice.id).label("total_invoices"),
            func.sum(Invoice.total_harga).label("total_amount"),
            func.count(func.filter(Invoice.status_invoice == "Lunas")).label("paid_invoices"),
        )
        .group_by(Invoice.pelanggan_id)
        .subquery()
    )

    # Query utama dengan statistik
    query = (
        select(Pelanggan, invoice_stats)
        .outerjoin(invoice_stats, Pelanggan.id == invoice_stats.c.pelanggan_id)
        .offset(skip)
        .limit(limit)
    )

    return query
