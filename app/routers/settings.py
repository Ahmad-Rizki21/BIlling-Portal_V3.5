from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth import get_current_active_user
from ..database import get_db
from ..models.system_setting import SystemSetting as SettingModel
from ..models.user import User as UserModel

router = APIRouter(prefix="/settings", tags=["System Settings"])


class SettingUpdate(BaseModel):
    value: str


@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Mengambil nilai sebuah pengaturan."""
    stmt = select(SettingModel).where(SettingModel.setting_key == key)
    setting = (await db.execute(stmt)).scalar_one_or_none()
    if not setting:
        return {"key": key, "value": None}
    return {"key": key, "value": setting.setting_value}


@router.put("/{key}")
async def update_setting(
    key: str,
    payload: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Memperbarui nilai sebuah pengaturan (Hanya Admin)."""
    # Pastikan hanya admin yang bisa mengubah
    if current_user.role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang dapat mengubah pengaturan.")

    stmt = select(SettingModel).where(SettingModel.setting_key == key)
    setting = (await db.execute(stmt)).scalar_one_or_none()

    if not setting:  # Jika belum ada, buat baru
        setting = SettingModel(setting_key=key, setting_value=payload.value)
    else:  # Jika sudah ada, update nilainya
        setting.setting_value = payload.value

    db.add(setting)
    await db.commit()
    return {"key": key, "value": payload.value}
