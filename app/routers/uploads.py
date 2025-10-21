# app/routers/uploads.py

import aiofiles
import secrets
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# Tentukan direktori untuk menyimpan file upload
UPLOAD_DIR = Path("static/uploads/speedtest")
EVIDENCE_DIR = Path("static/uploads/evidence")

# Buat direktori jika belum ada
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/speedtest/")
async def upload_speedtest_proof(file: UploadFile = File(...)):
    """
    Menerima file gambar, menyimpannya dengan nama unik,
    dan mengembalikan URL untuk mengaksesnya.
    """
    # Validasi tipe file (opsional tapi sangat disarankan)
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipe file tidak didukung. Harap unggah JPG, PNG, atau WEBP.",
        )

    # Buat nama file yang aman dan unik
    file_extension = Path(file.filename or "").suffix
    unique_filename = f"{secrets.token_hex(8)}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # Simpan file secara asinkron
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan file: {e}",
        )

    # Kembalikan URL yang bisa diakses oleh frontend
    file_url = f"/static/uploads/speedtest/{unique_filename}"
    return {"file_url": file_url}


@router.post("/evidence/")
async def upload_evidence_file(file: UploadFile = File(...)):
    """
    Upload evidence file untuk trouble ticket.
    Menerima berbagai tipe file dan menyimpannya dengan nama unik.
    """
    # Validasi tipe file yang diizinkan
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
        "application/pdf",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "application/zip", "application/x-rar-compressed",
        "video/mp4", "video/avi", "video/quicktime", "video/x-msvideo"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipe file tidak didukung. File yang diizinkan: Images, PDF, Office documents, ZIP, dan video.",
        )

    # Validasi ukuran file (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran file terlalu besar. Maksimal 10MB.",
        )

    # Buat nama file yang aman dan unik
    file_extension = Path(file.filename or "").suffix
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File harus memiliki ekstensi yang valid.",
        )

    unique_filename = f"{secrets.token_hex(12)}{file_extension}"
    file_path = EVIDENCE_DIR / unique_filename

    try:
        # Simpan file secara asinkron
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan file: {e}",
        )

    # Kembalikan URL yang bisa diakses oleh frontend
    file_url = f"/static/uploads/evidence/{unique_filename}"
    return {
        "file_url": file_url,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }
