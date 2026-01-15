"""
Instalasi Document API Router
Untuk upload dan manage foto-foto BA Instalasi
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import os
import uuid
import shutil
from pathlib import Path

from ..database import get_db
from ..models.instalasi_document import InstalasiDocument as InstalasiDocumentModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel
from ..models.work_order import WorkOrder as WorkOrderModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..auth import get_current_active_user

router = APIRouter(
    prefix="/instalasi",
    tags=["Instalasi Documents"],
)

# Configuration
UPLOAD_DIR = Path("storage/instalasi")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Document types yang diperbolehkan
ALLOWED_DOCUMENT_TYPES = [
    "photo_odp_before",
    "photo_odp_after",
    "photo_onu",
    "photo_speedtest",
    "signature_pelanggan",
    "signature_teknisi",
    "other"
]

# Allowed MIME types
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp"
]

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


async def get_document_type_name(document_type: str) -> str:
    """Convert document type code to display name"""
    names = {
        "photo_odp_before": "ODP (Sebelum)",
        "photo_odp_after": "ODP (Sesudah)",
        "photo_onu": "ONU/ONT Aktif",
        "photo_speedtest": "Speed Test",
        "signature_pelanggan": "Tanda Tangan Pelanggan",
        "signature_teknisi": "Tanda Tangan Teknisi",
        "other": "Lainnya"
    }
    return names.get(document_type, document_type)


@router.post("/{pelanggan_id}/upload")
async def upload_instalasi_document(
    pelanggan_id: int,
    document_type: str = Query(..., description="Type of document"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Upload foto untuk BA Instalasi

    Document types:
    - photo_odp_before: Foto ODP sebelum instalasi
    - photo_odp_after: Foto ODP sesudah instalasi
    - photo_onu: Foto ONU/ONT yang aktif
    - photo_speedtest: Foto hasil speed test
    - signature_pelanggan: Tanda tangan pelanggan
    - signature_teknisi: Tanda tangan teknisi
    - other: Dokumen lain
    """
    # Validate document type
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document_type. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
        )

    # Check if pelanggan exists
    result = await db.execute(select(PelangganModel).where(PelangganModel.id == pelanggan_id))
    pelanggan = result.scalar_one_or_none()
    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    # Get file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # Create pelanggan directory
    pelanggan_dir = UPLOAD_DIR / str(pelanggan_id)
    pelanggan_dir.mkdir(exist_ok=True)

    # Save file
    file_path = pelanggan_dir / unique_filename
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Save to database (delete existing if same document_type exists)
    # Delete existing document with same type
    existing_doc = await db.execute(
        select(InstalasiDocumentModel).where(
            and_(
                InstalasiDocumentModel.pelanggan_id == pelanggan_id,
                InstalasiDocumentModel.document_type == document_type
            )
        )
    )
    existing = existing_doc.scalar_one_or_none()
    if existing:
        # Delete old file
        old_file_path = Path(existing.file_path)
        if old_file_path.exists():
            old_file_path.unlink()
        # Delete from database
        await db.delete(existing)

    # Get the latest work order ID for this pelanggan
    work_order_id = None
    wo_result = await db.execute(
        select(WorkOrderModel).where(
            WorkOrderModel.pelanggan_id == pelanggan_id
        ).order_by(WorkOrderModel.id.desc()).limit(1)
    )
    latest_wo = wo_result.scalar_one_or_none()
    if latest_wo:
        work_order_id = latest_wo.id

    # Create new document record
    new_doc = InstalasiDocumentModel(
        pelanggan_id=pelanggan_id,
        work_order_id=work_order_id,
        document_type=document_type,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow()
    )

    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    return {
        "message": "Document uploaded successfully",
        "document": {
            "id": new_doc.id,
            "document_type": new_doc.document_type,
            "document_type_name": await get_document_type_name(new_doc.document_type),
            "file_name": new_doc.file_name,
            "file_size": new_doc.file_size,
            "uploaded_at": new_doc.uploaded_at.isoformat()
        }
    }


@router.get("/{pelanggan_id}/documents")
async def get_instalasi_documents(
    pelanggan_id: int,
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get semua instalasi documents untuk pelanggan"""
    # Check if pelanggan exists
    result = await db.execute(select(PelangganModel).where(PelangganModel.id == pelanggan_id))
    pelanggan = result.scalar_one_or_none()
    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    # Build query
    query = select(InstalasiDocumentModel).where(
        InstalasiDocumentModel.pelanggan_id == pelanggan_id
    )

    # Filter by document types if specified
    if document_types:
        query = query.where(InstalasiDocumentModel.document_type.in_(document_types))

    query = query.order_by(InstalasiDocumentModel.created_at.desc())

    result = await db.execute(query)
    documents = result.scalars().all()

    # Format response
    formatted_docs = []
    for doc in documents:
        formatted_docs.append({
            "id": doc.id,
            "document_type": doc.document_type,
            "document_type_name": await get_document_type_name(doc.document_type),
            "file_path": doc.file_path,
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "uploaded_by": doc.uploaded_by
        })

    return {
        "pelanggan_id": pelanggan_id,
        "documents": formatted_docs
    }


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download document by ID (returns file)"""
    from fastapi.responses import FileResponse

    # Get document
    result = await db.execute(
        select(InstalasiDocumentModel).where(InstalasiDocumentModel.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document tidak ditemukan")

    # Check if file exists
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    return FileResponse(
        path=str(file_path),
        filename=doc.file_name,
        media_type=doc.mime_type or "image/jpeg"
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete document"""
    # Get document
    result = await db.execute(
        select(InstalasiDocumentModel).where(InstalasiDocumentModel.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document tidak ditemukan")

    # Delete file
    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    await db.delete(doc)
    await db.commit()

    return {"message": "Document deleted successfully"}


@router.get("/{pelanggan_id}/documents/summary")
async def get_documents_summary(
    pelanggan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get summary of documents by type (untuk cek apa yang sudah diupload)"""
    # Check if pelanggan exists
    result = await db.execute(select(PelangganModel).where(PelangganModel.id == pelanggan_id))
    pelanggan = result.scalar_one_or_none()
    if not pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

    # Get all documents
    result = await db.execute(
        select(InstalasiDocumentModel).where(
            InstalasiDocumentModel.pelanggan_id == pelanggan_id
        )
    )
    documents = result.scalars().all()

    # Build summary
    summary = {}
    for doc_type in ALLOWED_DOCUMENT_TYPES:
        summary[doc_type] = {
            "name": await get_document_type_name(doc_type),
            "uploaded": False,
            "document_id": None,
            "uploaded_at": None
        }

    for doc in documents:
        if doc.document_type in summary:
            summary[doc.document_type] = {
                "name": await get_document_type_name(doc.document_type),
                "uploaded": True,
                "document_id": doc.id,
                "uploaded_at": doc.uploaded_at.isoformat()
            }

    return {
        "pelanggan_id": pelanggan_id,
        "summary": summary
    }
