from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import date
from fastapi.responses import StreamingResponse
import logging
import io
import csv

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User as UserModel
from ..schemas.pelanggan import (
    PaginatedPelangganResponse,
    Pelanggan as PelangganSchema,
    PelangganCreate,
    PelangganUpdate,
    PelangganListResponse,
)
from ..services.pelanggan_service import PelangganService, get_pelanggan_service
from ..utils.export import create_pelanggan_export_response

router = APIRouter(
    prefix="/pelanggan",
    tags=["Pelanggan"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


# CREATE /pelanggan/ - Membuat pelanggan baru
@router.post("/", response_model=PelangganSchema, status_code=status.HTTP_201_CREATED)
async def create_pelanggan(
    pelanggan: PelangganCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """
    Membuat pelanggan baru. 
    Menggunakan service layer untuk business logic dan integrasi notifikasi.
    """
    return await service.create_pelanggan(pelanggan.model_dump())


# GET /pelanggan/ - Ambil daftar pelanggan dengan filter
@router.get("/", response_model=PelangganListResponse)
async def read_all_pelanggan(
    skip: int = Query(0, ge=0),
    limit: int = Query(default=50, le=1000),
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    layanan: Optional[str] = None,
    tgl_instalasi_from: Optional[date] = None,
    tgl_instalasi_to: Optional[date] = None,
    connection_status: Optional[str] = Query(None, description="configured, unconfigured"),
    use_minimal_loading: bool = Query(False, description="Loading minimal data (faster)"),
    for_invoice_selection: bool = Query(False, description="Loading minimal data for invoice selection"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Mengambil daftar semua pelanggan dengan berbagai filter pencarian."""
    filters = {
        "skip": skip, "limit": limit, "search": search, "alamat": alamat,
        "id_brand": id_brand, "layanan": layanan,
        "tgl_instalasi_from": tgl_instalasi_from, "tgl_instalasi_to": tgl_instalasi_to,
        "connection_status": connection_status, "use_minimal_loading": use_minimal_loading,
        "for_invoice_selection": for_invoice_selection
    }
    data, total_count = await service.get_all_pelanggan(filters)
    return {"data": data, "total_count": total_count}


# GET /pelanggan/export - Export data pelanggan ke CSV/Excel
@router.get("/export", response_class=StreamingResponse)
async def export_data(
    skip: int = 0,
    limit: int = 3000,
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    layanan: Optional[str] = None,
    format: str = Query("csv"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Mengekspor data pelanggan dengan data relasi ke format CSV atau Excel."""
    filters = {
        "skip": skip, "limit": min(limit, 10000), "search": search, "alamat": alamat,
        "id_brand": id_brand, "layanan": layanan, "use_minimal_loading": True
    }
    data_list, _ = await service.get_all_pelanggan(filters)
    
    # Transform data for export
    export_data = []
    for d in data_list:
        export_data.append({
            "id": d.id,
            "no_ktp": d.no_ktp,
            "nama": d.nama,
            "email": d.email,
            "no_telp": d.no_telp,
            "alamat": d.alamat,
            "alamat_2": d.alamat_2,
            "blok": d.blok,
            "unit": d.unit,
            "tgl_instalasi": d.tgl_instalasi.strftime('%Y-%m-%d') if d.tgl_instalasi else "",
            "layanan": d.layanan,
            "id_brand": d.id_brand,
            "pppoe_id": d.data_teknis.id_pelanggan if d.data_teknis else "BELUM ADA",
            "ip_pelanggan": d.data_teknis.ip_pelanggan if d.data_teknis else "BELUM ADA",
        })

    return create_pelanggan_export_response(export_data, format.lower())


# GET /pelanggan/paginated - Ambil daftar pelanggan dengan paginasi
@router.get("/paginated", response_model=PaginatedPelangganResponse)
async def read_pelanggan_paginated(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    layanan: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Mengambil daftar pelanggan dengan informasi paginasi lengkap."""
    skip = (page - 1) * limit
    filters = {
        "skip": skip, "limit": limit, "search": search, "alamat": alamat,
        "id_brand": id_brand, "layanan": layanan
    }
    data, total_count = await service.get_all_pelanggan(filters)
    
    total_pages = (total_count + limit - 1) // limit
    pagination = {
        "totalItems": total_count,
        "currentPage": page,
        "itemsPerPage": limit,
        "totalPages": total_pages,
        "hasNext": page < total_pages,
        "hasPrevious": page > 1,
        "startIndex": skip,
        "endIndex": skip + len(data)
    }
    
    return {"data": data, "pagination": pagination}


# GET /pelanggan/{pelanggan_id} - Ambil satu pelanggan
@router.get("/{pelanggan_id}", response_model=PelangganSchema)
async def read_pelanggan_by_id(
    pelanggan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Mengambil data lengkap satu pelanggan berdasarkan ID."""
    data = await service.get_by_id_with_relations(pelanggan_id, ["harga_layanan", "data_teknis"])
    if not data:
        raise HTTPException(status_code=404, detail="Pelanggan not found")
    return data


# PATCH /pelanggan/{pelanggan_id} - Update pelanggan
@router.patch("/{pelanggan_id}", response_model=PelangganSchema)
async def update_pelanggan(
    pelanggan_id: int,
    pelanggan_update: PelangganUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Update detail data pelanggan secara parsial."""
    return await service.update_pelanggan(pelanggan_id, pelanggan_update.model_dump(exclude_unset=True))


# DELETE /pelanggan/{pelanggan_id} - Hapus pelanggan
@router.delete("/{pelanggan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pelanggan(
    pelanggan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Menghapus pelanggan dan semua data terkait (cascade delete)."""
    await service.delete_pelanggan_cascade(pelanggan_id)
    return None


# GET /pelanggan/template/csv - Download template import
@router.get("/template/csv", response_class=StreamingResponse)
async def download_csv_template():
    """Men-download template CSV untuk import data pelanggan."""
    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel
    headers = [
        "Nama", "No KTP", "Email", "No Telepon", "Alamat", "Alamat 2",
        "Blok", "Unit", "Tanggal Instalasi (YYYY-MM-DD)", "Layanan", "ID Brand"
    ]
    writer = io.StringIO()
    csv_writer = csv.DictWriter(writer, fieldnames=headers, delimiter=";")
    csv_writer.writeheader()
    csv_writer.writerow({
        "Nama": "Budi Santoso",
        "No KTP": "1234567890123456",
        "Email": "budi.s@example.com",
        "No Telepon": "08123456789",
        "Alamat": "Perumahan Indah",
        "Alamat 2": "Blok A No 1",
        "Blok": "A",
        "Unit": "1",
        "Tanggal Instalasi (YYYY-MM-DD)": "2024-01-15",
        "Layanan": "Internet 50 Mbps",
        "ID Brand": "AJN"
    })
    
    response_headers = {"Content-Disposition": 'attachment; filename="template_pelanggan.csv"'}
    return StreamingResponse(
        io.BytesIO(writer.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# POST /pelanggan/import - Import data dari CSV
@router.post("/import")
async def import_from_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Mengimpor data pelanggan secara massal dari file CSV."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be .csv")
    
    contents = await file.read()
    result = await service.bulk_import(contents, file.filename)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result)
    return result


# GET /pelanggan/lokasi/unik - Alamat unik
@router.get("/lokasi/unik", response_model=List[str])
async def get_unique_lokasi(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    service: PelangganService = Depends(get_pelanggan_service)
):
    """Ambil daftar lokasi/alamat unik pelanggan untuk filter dropdown."""
    return await service.get_unique_lokasi()
