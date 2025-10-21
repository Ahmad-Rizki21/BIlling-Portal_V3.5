import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth import get_current_active_user
from ..database import get_db
from ..models.olt import OLT as OLTModel
from ..models.user import User as UserModel
from ..schemas.olt import OLT as OLTSchema
from ..schemas.olt import OLTCreate, OLTUpdate
from ..security import decrypt_password, encrypt_password

router = APIRouter(prefix="/olt", tags=["OLT"])

logging.basicConfig(filename='netmiko_session.log', level=logging.DEBUG)
netmiko_logger = logging.getLogger("netmiko")

@router.post("/", response_model=OLTSchema, status_code=status.HTTP_201_CREATED)
async def create_olt(olt_data: OLTCreate, db: AsyncSession = Depends(get_db)):
    # Enkripsi password sebelum disimpan
    if olt_data.password:
        olt_data.password = encrypt_password(olt_data.password)
        
    db_olt = OLTModel(**olt_data.model_dump())
    db.add(db_olt)
    await db.commit()
    await db.refresh(db_olt)
    return db_olt

@router.get("/", response_model=List[OLTSchema])
async def get_all_olts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OLTModel))
    return result.scalars().all()

@router.patch("/{olt_id}", response_model=OLTSchema)
async def update_olt(olt_id: int, olt_data: OLTUpdate, db: AsyncSession = Depends(get_db)):
    db_olt = await db.get(OLTModel, olt_id)
    if not db_olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    
    update_data = olt_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_olt, key, value)
        
    db.add(db_olt)
    await db.commit()
    await db.refresh(db_olt)
    return db_olt

@router.delete("/{olt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_olt(olt_id: int, db: AsyncSession = Depends(get_db)):
    db_olt = await db.get(OLTModel, olt_id)
    if not db_olt:
        raise HTTPException(status_code=404, detail="OLT not found")
    await db.delete(db_olt)
    await db.commit()
    return None


def _perform_netmiko_connection(olt_details: dict):
    """
    Fungsi synchronous terpisah untuk menangani koneksi Netmiko.
    """
    try:
        # TAMBAHKAN 'session_log' untuk debugging
        olt_details['session_log'] = 'netmiko_session.log'
        olt_details['global_delay_factor'] = 2  # Memberi jeda lebih lama antar perintah
        olt_details['banner_timeout'] = 20      # Waktu tunggu lebih lama untuk banner login
        olt_details['blocking_timeout'] = 20    # Waktu tunggu lebih lama untuk eksekusi perintah
        
        with ConnectHandler(**olt_details) as net_connect:
            net_connect.find_prompt()
        return {"status": "success", "message": f"Koneksi ke {olt_details['host']} berhasil!"}
    
    except Exception as e:
        # Kita buat pesan error lebih detail untuk debugging
        netmiko_logger.error(f"NETMIKO FAILED: {str(e)}")
        
        if isinstance(e, NetmikoAuthenticationException):
            return {"status": "failure", "message": "Koneksi gagal: Username atau password salah."}
        if isinstance(e, NetmikoTimeoutException):
            return {"status": "failure", "message": "Koneksi gagal: Timeout. Pastikan IP dan port benar."}
        
        return {"status": "failure", "message": f"Terjadi error: {str(e)}"}


@router.post("/{olt_id}/test-connection")
async def test_olt_connection(
    olt_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_olt = await db.get(OLTModel, olt_id)
    if not db_olt:
        raise HTTPException(status_code=404, detail="OLT not found")

    if not db_olt.password or not db_olt.username:
        return JSONResponse(status_code=400, content={"status": "failure", "message": "Username atau password kosong."})

    try:
        decrypted_password = decrypt_password(db_olt.password)
    except Exception:
        return JSONResponse(status_code=400, content={"status": "failure", "message": "Password tersimpan tidak valid. Harap simpan ulang password."})

    device_type_map = { "hsgq": "generic_telnet", "zte": "zte_zxan_ssh" }
    device_type = device_type_map.get(db_olt.tipe_olt.lower(), "generic")

    olt_details = {
        'device_type': device_type,
        'host': db_olt.ip_address,
        'username': db_olt.username,
        'password': decrypted_password,
        'port': 23 if device_type == 'generic_telnet' else 22,
        'conn_timeout': 10,
    }

    # Jalankan fungsi helper synchronous di thread terpisah
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _perform_netmiko_connection, olt_details)

    # Kirim respons berdasarkan hasil dari fungsi helper
    if result["status"] == "success":
        return result
    else:
        # Jika gagal, kirim status error HTTP yang sesuai
        return JSONResponse(status_code=400, content=result)