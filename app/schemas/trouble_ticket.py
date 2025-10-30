from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

from .pelanggan import Pelanggan
from .data_teknis import DataTeknis
from .user import User
from .harga_layanan import HargaLayanan


# Enums untuk API
class TicketStatusEnum(str, Enum):
    """Enum untuk status trouble ticket"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_VENDOR = "pending_vendor"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketPriorityEnum(str, Enum):
    """Enum untuk prioritas trouble ticket"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategoryEnum(str, Enum):
    """Enum untuk kategori masalah"""
    NO_CONNECTION = "no_connection"
    SLOW_CONNECTION = "slow_connection"
    INTERMITTENT = "intermittent"
    HARDWARE_ISSUE = "hardware_issue"
    CABLE_ISSUE = "cable_issue"
    ONU_ISSUE = "onu_issue"
    OLT_ISSUE = "olt_issue"
    MIKROTIK_ISSUE = "mikrotik_issue"
    OTHER = "other"


# Skema untuk membuat Trouble Ticket baru
class TroubleTicketCreate(BaseModel):
    pelanggan_id: int = Field(..., gt=0, description="ID Pelanggan (wajib)")
    data_teknis_id: Optional[int] = Field(None, gt=0, description="ID Data Teknis (opsional)")
    title: str = Field(..., min_length=3, max_length=200, description="Judul ticket (wajib)")
    description: str = Field(..., min_length=10, description="Deskripsi masalah (wajib)")
    category: TicketCategoryEnum = Field(..., description="Kategori masalah (wajib)")
    priority: TicketPriorityEnum = Field(TicketPriorityEnum.MEDIUM, description="Prioritas ticket")
    assigned_to: Optional[int] = Field(None, gt=0, description="ID user yang ditugaskan (opsional)")
    evidence: Optional[str] = Field(None, description="Evidence files URLs (JSON array string)")

    @validator("title", pre=True)
    def validate_title(cls, v):
        if v is None:
            raise ValueError("Judul tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Judul tidak boleh kosong")

        if len(v_str) < 3:
            raise ValueError("Judul harus minimal 3 karakter")

        if len(v_str) > 200:
            raise ValueError("Judul maksimal 200 karakter")

        return v_str

    @validator("description", pre=True)
    def validate_description(cls, v):
        if v is None:
            raise ValueError("Deskripsi tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Deskripsi tidak boleh kosong")

        if len(v_str) < 10:
            raise ValueError("Deskripsi harus minimal 10 karakter")

        return v_str

    @validator("assigned_to", pre=True, always=True)
    def validate_assigned_to(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID user harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID user harus lebih dari 0")

        return v_int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "pelanggan_id": 1,
                "data_teknis_id": 1,
                "title": "Internet tidak bisa connect",
                "description": "Pelanggan melaporkan bahwa internet tidak bisa connect sejak jam 9 pagi",
                "category": "no_connection",
                "priority": "high",
                "assigned_to": 2
            }
        }


# Skema untuk update Trouble Ticket
class TroubleTicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[TicketCategoryEnum] = None
    priority: Optional[TicketPriorityEnum] = None
    status: Optional[TicketStatusEnum] = None
    assigned_to: Optional[int] = Field(None, gt=0)
    resolution_notes: Optional[str] = None
    customer_notified: Optional[bool] = None
    evidence: Optional[str] = None

    @validator("title", pre=True)
    def validate_title_update(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return v

        if len(v_str) < 3:
            raise ValueError("Judul harus minimal 3 karakter")

        if len(v_str) > 200:
            raise ValueError("Judul maksimal 200 karakter")

        return v_str

    @validator("description", pre=True)
    def validate_description_update(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return v

        if len(v_str) < 10:
            raise ValueError("Deskripsi harus minimal 10 karakter")

        return v_str

    @validator("assigned_to", pre=True, always=True)
    def validate_assigned_to_update(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID user harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID user harus lebih dari 0")

        return v_int

    class Config:
        from_attributes = True


# Skema untuk response Trouble Ticket
class TroubleTicket(BaseModel):
    id: int
    ticket_number: str
    pelanggan_id: int
    data_teknis_id: Optional[int] = None
    title: str
    description: str
    category: TicketCategoryEnum
    priority: TicketPriorityEnum
    status: TicketStatusEnum
    downtime_start: Optional[datetime] = None
    downtime_end: Optional[datetime] = None
    total_downtime_minutes: Optional[int] = None
    assigned_to: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    customer_notified: bool
    last_customer_contact: Optional[datetime] = None
    evidence: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Include related data when needed
    pelanggan: Optional[Pelanggan] = None
    data_teknis: Optional[DataTeknis] = None
    assigned_user: Optional[User] = None

    class Config:
        from_attributes = True


# Skema untuk Trouble Ticket dengan relasi lengkap
class TroubleTicketWithRelations(TroubleTicket):
    pelanggan: Pelanggan
    data_teknis: Optional[DataTeknis] = None
    assigned_user: Optional[User] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ticket_number": "TT-20250116-12345",
                "pelanggan_id": 1,
                "data_teknis_id": 1,
                "title": "Internet tidak bisa connect",
                "description": "Pelanggan melaporkan koneksi internet down",
                "category": "no_connection",
                "priority": "high",
                "status": "open",
                "downtime_start": "2025-01-16T09:00:00",
                "downtime_end": None,
                "total_downtime_minutes": 0,
                "assigned_to": 2,
                "resolved_at": None,
                "resolution_notes": None,
                "customer_notified": False,
                "last_customer_contact": None,
                "created_at": "2025-01-16T09:15:00",
                "updated_at": "2025-01-16T09:15:00",
                "pelanggan": {
                    "id": 1,
                    "nama": "Ahmad Rizki",
                    "alamat": "Jl. Contoh No. 123",
                    "no_telp": "081234567890",
                    "email": "ahmad@example.com",
                    "blok": "A",
                    "unit": "12",
                    "id_brand": "ajn-01",
                    "layanan": "Internet 50Mbps",
                    "harga_layanan": {
                        "id_brand": "ajn-01",
                        "brand": "JAKINET",
                        "pajak": 11.0
                    }
                },
                "data_teknis": {
                    "id": 1,
                    "ip_pelanggan": "192.168.1.100",
                    "password_pppoe": "secret123",
                    "onu_power": -15
                },
                "assigned_user": {
                    "id": 2,
                    "name": "Teknisi NOC"
                }
            }
        }


# Skema untuk update status ticket
class TicketStatusUpdate(BaseModel):
    status: TicketStatusEnum = Field(..., description="Status baru ticket")
    notes: Optional[str] = Field(None, description="Catatan perubahan status")
    action_description: Optional[str] = Field(None, description="Deskripsi tindakan yang diambil")
    summary_problem: Optional[str] = Field(None, description="Ringkasan masalah")
    summary_action: Optional[str] = Field(None, description="Ringkasan tindakan yang diambil")
    evidence: Optional[str] = Field(None, description="Bukti/evidence terkait tindakan")

    @validator("notes", pre=True)
    def validate_notes(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 1000:
            raise ValueError("Catatan maksimal 1000 karakter")

        return v_str

    @validator("action_description", pre=True)
    def validate_action_description(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 2000:
            raise ValueError("Deskripsi tindakan maksimal 2000 karakter")

        return v_str

    @validator("summary_problem", pre=True)
    def validate_summary_problem(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 1000:
            raise ValueError("Ringkasan masalah maksimal 1000 karakter")

        return v_str

    @validator("summary_action", pre=True)
    def validate_summary_action(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 1000:
            raise ValueError("Ringkasan tindakan maksimal 1000 karakter")

        return v_str

    @validator("evidence", pre=True)
    def validate_evidence(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 5000:
            raise ValueError("Evidence maksimal 5000 karakter")

        return v_str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "in_progress",
                "notes": "Sedang dalam perjalanan ke lokasi pelanggan",
                "action_description": "Melakukan pengecekan kabel dan peralatan",
                "summary_problem": "Koneksi internet down karena kabel terputus",
                "summary_action": "Mengganti kabel yang rusak",
                "evidence": "/uploads/evidence/ticket_123.jpg"
            }
        }


# Skema untuk downtime update
class DowntimeUpdate(BaseModel):
    downtime_start: Optional[datetime] = Field(None, description="Waktu mulai downtime")
    downtime_end: Optional[datetime] = Field(None, description="Waktu selesai downtime")

    @validator("downtime_start", pre=True)
    def validate_downtime_start(cls, v):
        if v is None:
            return v

        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Format waktu tidak valid")

        return v

    @validator("downtime_end", pre=True)
    def validate_downtime_end(cls, v):
        if v is None:
            return v

        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Format waktu tidak valid")

        return v

    class Config:
        from_attributes = True


# Skema untuk Ticket History
class TicketHistory(BaseModel):
    id: int
    ticket_id: int
    old_status: Optional[TicketStatusEnum] = None
    new_status: TicketStatusEnum
    changed_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    changed_user: Optional[User] = None

    class Config:
        from_attributes = True


# Skema untuk Action Taken
class ActionTaken(BaseModel):
    id: int
    ticket_id: int
    action_description: str
    summary_problem: str
    summary_action: str
    evidence: Optional[str] = None
    notes: Optional[str] = None
    taken_by: Optional[int] = None
    created_at: datetime
    taken_user: Optional[User] = None

    class Config:
        from_attributes = True


# Skema untuk pagination response
class PaginationInfo(BaseModel):
    totalItems: int = Field(..., ge=0, description="Total jumlah items")
    currentPage: int = Field(..., ge=1, description="Halaman saat ini")
    itemsPerPage: int = Field(..., ge=1, le=100, description="Jumlah items per halaman")
    totalPages: int = Field(..., ge=0, description="Total jumlah halaman")
    hasNext: bool = Field(..., description="Apakah ada halaman berikutnya")
    hasPrevious: bool = Field(..., description="Apakah ada halaman sebelumnya")

    class Config:
        from_attributes = True


# Skema response dengan pagination
class PaginatedTroubleTicketResponse(BaseModel):
    data: List[TroubleTicket] = Field(..., description="Daftar trouble tickets")
    pagination: PaginationInfo = Field(..., description="Informasi pagination")
    meta: dict = Field(default_factory=dict, description="Metadata tambahan")

    class Config:
        from_attributes = True


# Skema untuk filter ticket
class TicketFilter(BaseModel):
    status: Optional[TicketStatusEnum] = Field(None, description="Filter berdasarkan status")
    priority: Optional[TicketPriorityEnum] = Field(None, description="Filter berdasarkan prioritas")
    category: Optional[TicketCategoryEnum] = Field(None, description="Filter berdasarkan kategori")
    assigned_to: Optional[int] = Field(None, gt=0, description="Filter berdasarkan user yang ditugaskan")
    pelanggan_id: Optional[int] = Field(None, gt=0, description="Filter berdasarkan pelanggan")
    date_from: Optional[datetime] = Field(None, description="Filter tanggal dari")
    date_to: Optional[datetime] = Field(None, description="Filter tanggal sampai")
    search: Optional[str] = Field(None, max_length=100, description="Pencarian berdasarkan judul atau deskripsi")

    @validator("search", pre=True)
    def validate_search(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Pencarian maksimal 100 karakter")

        return v_str

    @validator("assigned_to", pre=True, always=True)
    def validate_assigned_to_filter(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID user harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID user harus lebih dari 0")

        return v_int

    @validator("pelanggan_id", pre=True, always=True)
    def validate_pelanggan_id_filter(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih dari 0")

        return v_int

    class Config:
        from_attributes = True


# Skema untuk dashboard statistics
class TicketStatistics(BaseModel):
    total_tickets: int = Field(..., ge=0, description="Total ticket")
    open_tickets: int = Field(..., ge=0, description="Ticket yang terbuka")
    in_progress_tickets: int = Field(..., ge=0, description="Ticket sedang dikerjakan")
    resolved_tickets: int = Field(..., ge=0, description="Ticket yang selesai")
    closed_tickets: int = Field(..., ge=0, description="Ticket yang ditutup")
    high_priority_tickets: int = Field(..., ge=0, description="Ticket prioritas tinggi")
    critical_priority_tickets: int = Field(..., ge=0, description="Ticket prioritas kritis")
    avg_resolution_time_hours: Optional[float] = Field(None, ge=0, description="Rata-rata waktu resolusi (jam)")
    tickets_this_month: int = Field(..., ge=0, description="Ticket bulan ini")
    unresolved_over_24h: int = Field(..., ge=0, description="Ticket belum terselesaikan > 24 jam")

    class Config:
        from_attributes = True


# Skema untuk assign ticket
class TicketAssignment(BaseModel):
    assigned_to: int = Field(..., gt=0, description="ID user yang akan ditugaskan")
    notes: Optional[str] = Field(None, description="Catatan penugasan")

    @validator("notes", pre=True)
    def validate_assignment_notes(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 500:
            raise ValueError("Catatan penugasan maksimal 500 karakter")

        return v_str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "assigned_to": 2,
                "notes": "Silakan dicek koneksi internet pelanggan"
            }
        }