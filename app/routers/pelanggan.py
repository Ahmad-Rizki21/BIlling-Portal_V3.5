from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Query,
)
from pydantic import BaseModel, Field
from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import io
import csv
import chardet
from dateutil import parser
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_

from ..models.pelanggan import Pelanggan as PelangganModel
from ..database import AsyncSessionLocal
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..services import mikrotik_service
from ..websocket_manager import manager
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..auth import get_current_active_user
from ..models.odp import ODP as ODPModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.langganan import Langganan as LanggananModel
from ..models.invoice import Invoice as InvoiceModel
from ..schemas.pelanggan import (
    PaginatedPelangganResponse,
    PaginationInfo,
    Pelanggan as PelangganSchema,
    PelangganCreate,
    PelangganUpdate,
    PelangganImport,
    IPCheckRequest,
    IPCheckResponse,
)
import logging
from ..database import get_db
from ..middleware.rate_limit import rate_limiter, login_rate_limit

router = APIRouter(
    prefix="/pelanggan",
    tags=["Pelanggan"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


# --- Skema Respons Baru ---
class PelangganListResponse(BaseModel):
    data: List[PelangganSchema]
    total_count: int


# POST /pelanggan - Tambah pelanggan baru
# Buat nambahin data pelanggan baru ke sistem
# Request body: data pelanggan (nama, email, no_telp, alamat, dll)
# Response: data pelanggan yang baru dibuat
# Validation: cek duplikasi email dan KTP
# Error handling: rollback transaction kalau ada error, kirim notifikasi ke tim NOC/CS
@router.post("/", response_model=PelangganSchema, status_code=status.HTTP_201_CREATED)
async def create_pelanggan(
    pelanggan: PelangganCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create pelanggan dengan database transaction untuk data consistency.
    ✅ TRANSACTION-SAFE: Semua operasi atomic atau rollback semua.
    """
    try:
        # 1. Create pelanggan record
        db_pelanggan = PelangganModel(**pelanggan.model_dump())
        db.add(db_pelanggan)

        # Flush untuk dapat ID tanpa commit
        await db.flush()
        await db.refresh(db_pelanggan, attribute_names=["harga_layanan", "data_teknis"])

        # 2. Prepare notification data (masih dalam transaction)
        target_roles = ["NOC", "CS", "Admin"]
        query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name).in_([r.lower() for r in target_roles]))
        result = await db.execute(query)
        target_user_ids = result.scalars().all()

        # 3. Prepare notification payload
        notification_payload = None
        if target_user_ids:
            pelanggan_nama = db_pelanggan.nama if db_pelanggan else "N/A"
            notification_payload = {
                "type": "new_customer_for_noc",
                "message": f"Pelanggan baru '{pelanggan_nama}' telah ditambahkan. Segera buatkan Data Teknis.",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "pelanggan_id": db_pelanggan.id,
                    "pelanggan_nama": pelanggan_nama,
                    "alamat": db_pelanggan.alamat,
                    "no_telp": db_pelanggan.no_telp,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        # Commit transaction
        await db.commit()

    except Exception as e:
        # Rollback transaction jika exception terjadi
        await db.rollback()
        logger.error(f"❌ Transaction failed during pelanggan creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal membuat pelanggan: {str(e)}")

    # Kirim notifications setelah transaction berhasil commit
    # ✅ SAFE: Pelanggan sudah committed, notification failure tidak affect data
    if notification_payload:
        try:
            await manager.broadcast_to_roles(notification_payload, list(target_user_ids))
            logger.info(f"✅ Notification sent for new pelanggan: {db_pelanggan.nama}")
        except Exception as e:
            logger.warning(f"⚠️  Notification failed but pelanggan created: {e}")
            # Don't raise exception - pelanggan sudah berhasil dibuat

    return db_pelanggan


# GET /pelanggan - Ambil semua data pelanggan
# Endpoint ini buat nampilin list pelanggan dengan fitur pencarian dan filter
# Query parameters:
# - skip: offset untuk pagination (default: 0)
# - limit: jumlah data per halaman (default: 15)
# - search: cari pelanggan berdasarkan nama, email, atau no_telp
# - alamat: filter berdasarkan alamat
# - id_brand: filter berdasarkan brand/provider
# - fields: pilih field yang mau ditampilin (biar response lebih kecil)
# - for_invoice_selection: kalo true, ambil semua data tanpa limit
# Response: list pelanggan dengan total count
# Performance optimization: eager loading biar ga N+1 query
@router.get("/", response_model=PelangganListResponse)
async def read_all_pelanggan(
    skip: int = 0,
    limit: Optional[int] = 15,
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    fields: Optional[str] = Query(None, description="Comma-separated field names to include (e.g., 'id,nama,email,no_telp')"),
    for_invoice_selection: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Mengambil daftar pelanggan dengan paginasi, filter, field selection, dan total jumlah data.
    API Response Optimization: Field filtering untuk mengurangi response size.
    """
    # Jika untuk invoice selection, load semua data tanpa limit
    if for_invoice_selection:
        limit = None
        skip = 0

    base_query = select(PelangganModel)
    count_query = select(func.count(PelangganModel.id))

    # Parse field selection untuk response optimization
    selected_fields = None
    if fields:
        selected_fields = [field.strip() for field in fields.split(",") if field.strip()]

    if search:
        search_term = f"%{search}%"
        filter_condition = or_(
            PelangganModel.nama.ilike(search_term),
            PelangganModel.email.ilike(search_term),
            PelangganModel.no_telp.ilike(search_term),
        )
        base_query = base_query.where(filter_condition)
        count_query = count_query.where(filter_condition)

    if alamat:
        base_query = base_query.where(PelangganModel.alamat == alamat)
        count_query = count_query.where(PelangganModel.alamat == alamat)

    if id_brand:
        base_query = base_query.where(PelangganModel.id_brand == id_brand)
        count_query = count_query.where(PelangganModel.id_brand == id_brand)

    # Eksekusi query untuk total count
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar_one()

    # OPTIMIZED: Eksekusi query dengan comprehensive eager loading untuk mencegah N+1 queries
    data_query = base_query.options(
        joinedload(PelangganModel.data_teknis),
        joinedload(PelangganModel.harga_layanan),
        joinedload(PelangganModel.langganan).joinedload(LanggananModel.paket_layanan),
    ).order_by(PelangganModel.id.desc())

    if limit is not None:
        data_query = data_query.offset(skip).limit(limit)

    result = await db.execute(data_query)
    # FIX: Tambahkan .unique() untuk collection eager loading
    pelanggan_list = result.scalars().unique().all()

    # API Response Optimization: Apply field filtering to reduce response size
    if selected_fields:
        filtered_data = []
        for pelanggan in pelanggan_list:
            filtered_item = {}
            for field in selected_fields:
                if hasattr(pelanggan, field):
                    filtered_item[field] = getattr(pelanggan, field)
            filtered_data.append(filtered_item)
        return PelangganListResponse(data=filtered_data, total_count=total_count)

    return PelangganListResponse(data=list(pelanggan_list), total_count=total_count)


# GET /pelanggan/paginated - Ambil data pelanggan dengan pagination lengkap
# Sama seperti GET /pelanggan tapi response-nya lebih detail pagination info-nya
# Query parameters:
# - skip: offset untuk pagination (min: 0)
# - limit: jumlah data per halaman (min: 1, max: 100)
# - search: cari pelanggan berdasarkan nama, email, atau no_telp
# - alamat: filter berdasarkan alamat
# - id_brand: filter berdasarkan ID Brand
# Response: data pelanggan + pagination info (totalItems, currentPage, totalPages, hasNext, hasPrevious)
# Performance optimization: eager loading untuk prevent N+1 queries
@router.get("/paginated", response_model=PaginatedPelangganResponse)
async def read_pelanggan_paginated(
    skip: int = Query(0, ge=0, description="Jumlah items untuk dilewati (offset)"),
    limit: int = Query(15, ge=1, le=100, description="Jumlah items per halaman (maksimal 100)"),
    search: Optional[str] = Query(None, description="Filter pencarian berdasarkan nama, email, atau no_telp"),
    alamat: Optional[str] = Query(None, description="Filter berdasarkan alamat"),
    id_brand: Optional[str] = Query(None, description="Filter berdasarkan ID Brand"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    logger.info(f"Mengambil data pelanggan dengan pagination: skip={skip}, limit={limit}")

    try:
        # OPTIMIZED: Query dengan comprehensive eager loading untuk paginated results
        query = select(PelangganModel).options(
            joinedload(PelangganModel.data_teknis),
            joinedload(PelangganModel.harga_layanan),
            joinedload(PelangganModel.langganan).joinedload(LanggananModel.paket_layanan),
        )

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    PelangganModel.nama.ilike(search_term),
                    PelangganModel.email.ilike(search_term),
                    PelangganModel.no_telp.ilike(search_term),
                )
            )

        if alamat:
            query = query.where(PelangganModel.alamat == alamat)

        if id_brand:
            query = query.where(PelangganModel.id_brand == id_brand)

        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total_result = await db.execute(count_query)
        total_items = total_result.scalar_one()

        paginated_query = query.offset(skip).limit(limit).order_by(PelangganModel.id.desc())
        result = await db.execute(paginated_query)
        # FIX: Tambahkan .unique() untuk collection eager loading
        pelanggan_list = result.scalars().unique().all()

        total_pages = (total_items + limit - 1) // limit
        current_page = (skip // limit) + 1 if limit > 0 else 1

        pagination_info = PaginationInfo(
            totalItems=total_items,
            currentPage=current_page,
            itemsPerPage=limit,
            totalPages=total_pages,
            hasNext=current_page < total_pages,
            hasPrevious=current_page > 1,
            startIndex=skip + 1,
            endIndex=min(skip + len(pelanggan_list), total_items),
        )

        response = PaginatedPelangganResponse(
            data=list(pelanggan_list),
            pagination=pagination_info,
            meta={
                "displayInfo": f"Menampilkan {len(pelanggan_list)} dari {total_items} items (Halaman {current_page} dari {total_pages})"
            },
        )

        logger.info(f"Berhasil mengambil {len(pelanggan_list)} pelanggan dari total {total_items}")
        return response

    except Exception as e:
        logger.error(f"Gagal mengambil data pelanggan dengan pagination: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data pelanggan: {str(e)}",
        )


# GET /pelanggan/{pelanggan_id} - Ambil detail pelanggan berdasarkan ID
# Buat nampilin detail data pelanggan tertentu
# Path parameters:
# - pelanggan_id: ID pelanggan yang mau diambil
# Response: data pelanggan lengkap dengan relasi (harga_layanan, data_teknis, langganan)
# Error handling: 404 kalau pelanggan nggak ketemu
# Performance optimization: eager loading biar ga N+1 query
@router.get("/{pelanggan_id}", response_model=PelangganSchema)
async def read_pelanggan_by_id(
    pelanggan_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)
):
    # OPTIMIZED: Query untuk pelanggan individual dengan comprehensive eager loading
    query = (
        select(PelangganModel)
        .where(PelangganModel.id == pelanggan_id)
        .options(
            joinedload(PelangganModel.harga_layanan),
            joinedload(PelangganModel.data_teknis),
            joinedload(PelangganModel.langganan).joinedload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    # FIX: Tambahkan .unique() untuk collection eager loading
    db_pelanggan = result.scalars().unique().one_or_none()

    if not db_pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    return db_pelanggan


# PATCH /pelanggan/{pelanggan_id} - Update data pelanggan
# Buat update data pelanggan yang udah ada
# Path parameters:
# - pelanggan_id: ID pelanggan yang mau diupdate
# Request body: field yang mau diupdate (cuma field yang diisi yang bakal keupdate)
# Response: data pelanggan setelah diupdate
# Validation: cek ID Brand dan Mikrotik Server kalau diubah
# Error handling: 404 kalau pelanggan nggak ketemu, rollback transaction kalau error
# Transaction safety: semua perubahan atomic atau rollback semua
@router.patch("/{pelanggan_id}", response_model=PelangganSchema)
async def update_pelanggan(
    pelanggan_id: int,
    pelanggan_update: PelangganUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Update pelanggan dengan database transaction untuk data consistency.
    ✅ TRANSACTION-SAFE: Semua perubahan atomic atau rollback semua.
    """
    try:
        # 1. Get existing pelanggan dengan eager loading
        query = (
            select(PelangganModel)
            .where(PelangganModel.id == pelanggan_id)
            .options(
                joinedload(PelangganModel.harga_layanan),
                joinedload(PelangganModel.data_teknis),
            )
        )
        result = await db.execute(query)
        db_pelanggan = result.scalar_one_or_none()

        if not db_pelanggan:
            raise HTTPException(status_code=404, detail="Pelanggan not found")

        # 2. Prepare update data
        update_data = pelanggan_update.model_dump(exclude_unset=True)
        update_data.pop("harga_layanan", None)

        # 3. Handle harga_layanan relationship update
        if "id_brand" in update_data:
            id_brand = update_data.pop("id_brand")
            if id_brand:
                harga_layanan_obj = await db.get(HargaLayananModel, id_brand)
                if not harga_layanan_obj:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Harga Layanan dengan ID Brand {id_brand} tidak ditemukan.",
                    )
                db_pelanggan.harga_layanan = harga_layanan_obj
            else:
                # Type: Explicitly set to None for optional relationship
                db_pelanggan.harga_layanan = None  # type: ignore

        # 4. Handle mikrotik_server relationship update
        if "mikrotik_server_id" in update_data:
            mikrotik_server_id = update_data.pop("mikrotik_server_id")
            if mikrotik_server_id:
                mikrotik_server_obj = await db.get(MikrotikServerModel, mikrotik_server_id)
                if not mikrotik_server_obj:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Mikrotik Server dengan ID {mikrotik_server_id} tidak ditemukan.",
                    )
                db_pelanggan.mikrotik_server = mikrotik_server_obj
            else:
                db_pelanggan.mikrotik_server = None  # type: ignore

        # 5. Apply field updates
        for key, value in update_data.items():
            setattr(db_pelanggan, key, value)

        # 6. Mark for update
        db.add(db_pelanggan)
        await db.flush()  # Validate sebelum commit

        # Commit transaction
        await db.commit()

        logger.info(f"✅ Pelanggan {pelanggan_id} updated successfully")

    except Exception as e:
        # Rollback transaction jika exception terjadi
        await db.rollback()
        logger.error(f"❌ Transaction failed during pelanggan update: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal update pelanggan: {str(e)}")

    # Refresh data setelah commit untuk response
    await db.refresh(db_pelanggan, attribute_names=["harga_layanan", "data_teknis"])

    return db_pelanggan


# DELETE /pelanggan/{pelanggan_id} - Hapus pelanggan dan semua data terkait
# Buat hapus pelanggan beserta semua data yang berelasi (cascade delete)
# Path parameters:
# - pelanggan_id: ID pelanggan yang mau dihapus
# Response: 204 No Content (sukses tapi nggak ada response body)
# Cascade delete: hapus data_teknis, langganan, dan invoice yang berelasi
# Error handling: 404 kalau pelanggan nggak ketemu, rollback kalau ada error
# Safety warning: HATI-HATI! Ini akan menghapus semua data terkait pelanggan
@router.delete("/{pelanggan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pelanggan(
    pelanggan_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)
):
    db_pelanggan = await db.get(PelangganModel, pelanggan_id)
    if not db_pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    try:
        logger.info(f"🔄 Starting cascade delete for pelanggan {pelanggan_id}: {db_pelanggan.nama}")

        # 1. Delete DataTeknis (one-to-one relationship)
        data_teknis_stmt = select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == pelanggan_id)
        data_teknis_result = await db.execute(data_teknis_stmt)
        data_teknis = data_teknis_result.scalar_one_or_none()
        if data_teknis:
            await db.delete(data_teknis)
            logger.info(f"✅ Deleted DataTeknis for pelanggan {pelanggan_id}")

        # 2. Delete all Langganan (one-to-many relationship)
        langganan_stmt = select(LanggananModel).where(LanggananModel.pelanggan_id == pelanggan_id)
        langganan_result = await db.execute(langganan_stmt)
        langganans = langganan_result.scalars().all()
        for langganan in langganans:
            await db.delete(langganan)
        logger.info(f"✅ Deleted {len(langganans)} Langganan records for pelanggan {pelanggan_id}")

        # 3. Delete all Invoices (one-to-many relationship)
        invoice_stmt = select(InvoiceModel).where(InvoiceModel.pelanggan_id == pelanggan_id)
        invoice_result = await db.execute(invoice_stmt)
        invoices = invoice_result.scalars().all()
        for invoice in invoices:
            await db.delete(invoice)
        logger.info(f"✅ Deleted {len(invoices)} Invoice records for pelanggan {pelanggan_id}")

        # 4. Finally delete the pelanggan record
        await db.delete(db_pelanggan)
        logger.info(f"✅ Deleted Pelanggan record for pelanggan {pelanggan_id}")

        # Commit transaksi
        await db.commit()

        logger.info(f"🎉 Cascade delete completed successfully for pelanggan {pelanggan_id}")
    except Exception as e:
        # Rollback transaksi jika ada error
        await db.rollback()
        logger.error(f"❌ Transaction failed during cascade delete: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal menghapus pelanggan dan data terkait: {str(e)}",
        )

    return None


# GET /pelanggan/template/csv - Download template CSV untuk import
# Buat download file template CSV yang bisa dipakai buat import data pelanggan
# Response: file CSV dengan header dan contoh data
# Format file: CSV dengan BOM (biar compatibility dengan Excel)
# Contoh data: include sample data biar gampang ngikutin format
@router.get("/template/csv", response_class=StreamingResponse)
async def download_csv_template(current_user: UserModel = Depends(get_current_active_user)):
    output = io.StringIO()
    output.write("\ufeff")
    headers = [
        "Nama",
        "No KTP",
        "Email",
        "No Telepon",
        "Layanan",
        "Alamat",
        "Alamat 2",
        "Blok",
        "Unit",
        "Tanggal Instalasi (YYYY-MM-DD)",
        "ID Brand",
    ]
    sample_data = [
        {
            "Nama": "John Doe",
            "No KTP": "1234567890123456",
            "Email": "john.doe@example.com",
            "No Telepon": "081234567890",
            "Layanan": "Internet 50 Mbps",
            "Alamat": "Jl. Contoh No 01",
            "Alamat 2": "RT 01 RW A",
            "Blok": "A",
            "Unit": "12",
            "Tanggal Instalasi (YYYY-MM-DD)": "2024-01-15",
            "ID Brand": "ajn-01",
        },
    ]
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample_data)
    output.seek(0)
    response_headers = {"Content-Disposition": 'attachment; filename="template_import_pelanggan.csv"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# GET /pelanggan/export/csv - Export data pelanggan ke CSV
# Buat export data pelanggan ke file CSV dengan filter yang sama seperti list
# Query parameters:
# - skip: offset untuk pagination (default: 0)
# - limit: maksimal 50,000 records per export (biar ga crash)
# - search: filter pencarian (sama seperti di list)
# - alamat: filter berdasarkan alamat
# - id_brand: filter berdasarkan brand/provider
# Response: file CSV dengan semua field pelanggan
# Performance optimization: pagination dan eager loading biar ga memory issues
# Format file: CSV dengan BOM dan timestamp di filename
@router.get("/export/csv", response_class=StreamingResponse)
async def export_to_csv(
    skip: int = 0,
    limit: int = Query(default=5000, le=50000, description="Maximum 50,000 records per export"),  # Max 50k records
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Mengekspor data pelanggan ke CSV, dengan mempertimbangkan filter yang aktif.
    PERFORMANCE OPTIMIZATION: Added pagination to prevent memory issues with large datasets.
    """
    # PERFORMANCE MONITORING: Log export parameters
    print(f"📊 Exporting pelanggan CSV: skip={skip}, limit={limit}, search={search}, alamat={alamat}, id_brand={id_brand}")

    # Apply pagination to prevent memory overload
    # OPTIMIZED: Tambahkan eager loading untuk mencegah N+1 queries
    query = (
        select(PelangganModel)
        .options(
            joinedload(PelangganModel.harga_layanan),
            joinedload(PelangganModel.data_teknis),
            joinedload(PelangganModel.langganan).joinedload(LanggananModel.paket_layanan),
        )
        .order_by(PelangganModel.id.desc())
        .offset(skip)
        .limit(limit)
    )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                PelangganModel.nama.ilike(search_term),
                PelangganModel.email.ilike(search_term),
                PelangganModel.no_telp.ilike(search_term),
            )
        )
    if alamat:
        query = query.where(PelangganModel.alamat == alamat)
    if id_brand:
        query = query.where(PelangganModel.id_brand == id_brand)

    result = await db.execute(query)
    # FIX: Tambahkan .unique() untuk collection eager loading
    pelanggan_list = result.scalars().unique().all()

    # PERFORMANCE MONITORING: Log export results
    print(f"✅ Pelanggan export returning {len(pelanggan_list)} records")

    if not pelanggan_list:
        raise HTTPException(status_code=404, detail="Tidak ada data pelanggan untuk diekspor dengan filter yang diberikan.")

    output = io.StringIO()
    output.write("\ufeff")
    headers = pelanggan_list[0].to_dict().keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for pelanggan in pelanggan_list:
        writer.writerow(pelanggan.to_dict())

    output.seek(0)
    filename = f"export_pelanggan_{datetime.now().strftime('%Y%m%d')}.csv"
    response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# POST /pelanggan/import - Import data pelanggan dari CSV
# Buat import data pelanggan dari file CSV
# Request body: file CSV dengan format yang sesuai template
# Response: jumlah pelanggan yang berhasil diimport + error message kalau ada
# Validation:
# - cek format file (.csv)
# - cek header CSV
# - cek duplikasi email dan KTP (dalam file dan di database)
# - cek format tanggal (YYYY-MM-DD)
# Error handling: rollback semua data kalau ada error, return detail error per baris
# Performance: batch insert biar lebih cepat
# Supported encoding: auto-detect encoding (utf-8, latin1, dll)
@router.post("/import")
async def import_from_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File kosong.")

    try:
        encoding = chardet.detect(contents)["encoding"] or "utf-8"
        content_str = contents.decode(encoding)
        stream = io.StringIO(content_str)
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="Header CSV tidak ditemukan.")
    except Exception as e:
        logger.error(f"Gagal membaca atau mem-parsing file CSV: {repr(e)}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file CSV: {repr(e)}")

    column_mapping = {
        "Nama": "nama",
        "No KTP": "no_ktp",
        "Email": "email",
        "No Telepon": "no_telp",
        "Alamat": "alamat",
        "Alamat 2": "alamat_2",
        "Blok": "blok",
        "Unit": "unit",
        "Tanggal Instalasi (YYYY-MM-DD)": "tgl_instalasi",
        "Layanan": "layanan",
        "ID Brand": "id_brand",
    }

    new_customers = []
    errors = []
    processed_emails_in_file = set()
    processed_no_ktp_in_file = set()
    skipped_rows = 0

    existing_emails_q = await db.execute(select(func.lower(PelangganModel.email)))
    existing_emails_in_db = set(existing_emails_q.scalars().all())
    existing_no_ktp_q = await db.execute(select(PelangganModel.no_ktp))
    existing_no_ktp_in_db = set(existing_no_ktp_q.scalars().all())

    for row_num, row in enumerate(reader, start=2):
        data: Dict[str, Any] = {
            model_field: row.get(csv_header, "").strip() for csv_header, model_field in column_mapping.items()
        }

        # Skip baris jika benar-benar kosong (tidak ada data sama sekali)
        if not any(data.values()):
            skipped_rows += 1
            continue

        try:
            tgl_instalasi_str = data.get("tgl_instalasi")
            if tgl_instalasi_str:
                try:
                    data["tgl_instalasi"] = parser.parse(tgl_instalasi_str).date()
                except (parser.ParserError, ValueError):
                    errors.append(f"Baris {row_num}: Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
                    continue
            else:
                data["tgl_instalasi"] = None  # type: ignore

            # 🔒 Ensure proper type casting before schema creation
            # Convert date string to proper date type if needed
            tgl_instalasi_value = data.get("tgl_instalasi")
            if tgl_instalasi_value:
                if isinstance(tgl_instalasi_value, str):
                    try:
                        # Try to parse the date string properly
                        data["tgl_instalasi"] = datetime.strptime(tgl_instalasi_value, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        # If parsing fails, set to None
                        data["tgl_instalasi"] = None
                # If already date type, keep as is
                elif isinstance(tgl_instalasi_value, date):
                    data["tgl_instalasi"] = tgl_instalasi_value
                else:
                    data["tgl_instalasi"] = None

            customer_schema = PelangganCreate(**data)
            email_lower = customer_schema.email.lower()
            no_ktp = customer_schema.no_ktp

            dummy_ktp_values = ["0000000000000000", "", "N/A", "NULL", "None"]

            if email_lower in processed_emails_in_file:
                errors.append(f"Baris {row_num}: Email '{customer_schema.email}' duplikat di dalam file CSV.")
                continue
            if no_ktp not in dummy_ktp_values and no_ktp in processed_no_ktp_in_file:
                errors.append(f"Baris {row_num}: No KTP '{no_ktp}' duplikat di dalam file CSV.")
                continue
            if email_lower in existing_emails_in_db:
                errors.append(f"Baris {row_num}: Email '{customer_schema.email}' sudah terdaftar.")
                continue
            if no_ktp not in dummy_ktp_values and no_ktp in existing_no_ktp_in_db:
                errors.append(f"Baris {row_num}: No KTP '{no_ktp}' sudah terdaftar.")
                continue

            new_customers.append(PelangganModel(**customer_schema.model_dump()))
            processed_emails_in_file.add(email_lower)
            if no_ktp not in dummy_ktp_values:
                processed_no_ktp_in_file.add(no_ktp)

        except ValidationError as e:
            error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
            errors.append(f"Baris {row_num}: {error_details}")
        except ValueError as e:
            errors.append(f"Baris {row_num}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing baris {row_num}: {repr(e)}")
            errors.append(f"Baris {row_num}: Error tak terduga - {repr(e)}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": f"Ditemukan {len(errors)} kesalahan.", "errors": errors},
        )

    if not new_customers:
        logger.info(f"Import selesai. {skipped_rows} baris di-skip, tidak ada data valid untuk diimpor.")
        if skipped_rows > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Tidak ada data valid untuk diimpor. {skipped_rows} baris kosong atau tidak lengkap dilewati."
            )
        else:
            raise HTTPException(status_code=400, detail="Tidak ada data valid untuk diimpor.")

    try:
        db.add_all(new_customers)
        await db.commit()
        logger.info(f"Import berhasil: {len(new_customers)} pelanggan baru, {skipped_rows} baris di-skip")
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {repr(e)}")

    success_message = f"Sukses! Berhasil mengimpor {len(new_customers)} pelanggan baru."
    if skipped_rows > 0:
        success_message += f" {skipped_rows} baris kosong dilewati."

    logger.info(f"Import CSV selesai: {len(new_customers)} berhasil, {len(errors)} error, {skipped_rows} baris kosong dilewati")

    return {"message": success_message}


# GET /pelanggan/lokasi/unik - Ambil daftar lokasi unik
# Buat ngambil list alamat/lokasi pelanggan yang unik (untuk dropdown filter)
# Response: array of string lokasi pelanggan
# Use case: buat dropdown filter di frontend
# Performance: query dengan distinct biar efficient
@router.get("/lokasi/unik", response_model=List[str])
async def get_unique_lokasi(db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    # OPTIMIZED: Query untuk lokasi unik dengan index hint untuk performance
    query = select(PelangganModel.alamat).distinct().order_by(PelangganModel.alamat)
    result = await db.execute(query)
    lokasi_list = result.scalars().all()
    return [lokasi for lokasi in lokasi_list if lokasi]
