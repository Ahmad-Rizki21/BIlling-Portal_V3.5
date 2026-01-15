# ====================================================================
# SCHEMA WORK ORDER - VALIDASI DATA WO
# ====================================================================
# Schema untuk validasi data Work Order yang masuk melalui API.
# Terdiri dari:
# - WorkOrderBase: Field dasar WO
# - WorkOrderCreate: Untuk membuat WO baru
# - WorkOrder: Untuk response API (dengan timestamps)
# - WorkOrderUpdate: Untuk update WO (semua field opsional)
# ====================================================================

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ==================== WORK ORDER SCHEMAS ====================

class WorkOrderBase(BaseModel):
    """Field dasar Work Order"""
    no_wo: str = Field(..., min_length=1, max_length=191, description="Nomor Work Order (format: FTTH - 01 - NEW INSTALLATION)")
    jenis_wo: str = Field(..., min_length=1, max_length=191, description="Jenis WO: new installation/relokasi/upgrade/downgrade")
    prioritas: str = Field(..., min_length=1, max_length=191, description="Prioritas: high/medium/low")
    tanggal_wo: date = Field(..., description="Tanggal pembuatan WO")
    tanggal_target_online: Optional[date] = Field(None, description="Target tanggal online")
    status: str = Field(default="pending", description="Status: pending/in_progress/completed/cancelled")
    catatan: Optional[str] = Field(None, max_length=500, description="Catatan tambahan")


class WorkOrderCreate(WorkOrderBase):
    """Schema untuk membuat Work Order baru"""
    pelanggan_id: int = Field(..., description="ID Pelanggan")


class WorkOrderUpdate(BaseModel):
    """Schema untuk update Work Order (semua field opsional)"""
    no_wo: Optional[str] = Field(None, min_length=1, max_length=191)
    jenis_wo: Optional[str] = Field(None, min_length=1, max_length=191)
    prioritas: Optional[str] = Field(None, min_length=1, max_length=191)
    tanggal_wo: Optional[date] = None
    tanggal_target_online: Optional[date] = None
    status: Optional[str] = None
    catatan: Optional[str] = Field(None, max_length=500)


class WorkOrder(WorkOrderBase):
    """Schema untuk menampilkan data Work Order (dengan timestamps)"""
    id: int
    pelanggan_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== WORK ORDER HISTORY ====================

class WorkOrderHistory(BaseModel):
    """Schema untuk menampilkan history WO pelanggan"""
    id: int
    no_wo: str
    jenis_wo: str
    prioritas: str
    tanggal_wo: date
    tanggal_target_online: Optional[date] = None
    status: str
    catatan: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
