# app/routers/uploads.py

import secrets
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile, status

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# Tentukan direktori untuk menyimpan file upload
UPLOAD_DIR = Path("static/uploads/speedtest")
# Buat direktori jika belum ada
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
