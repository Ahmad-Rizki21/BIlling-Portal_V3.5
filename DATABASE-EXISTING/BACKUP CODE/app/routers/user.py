import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # <-- Pastikan diimpor

from .. import auth
from ..auth import (  # <-- Impor get_password_hash dari auth
    get_current_active_user,
    get_password_hash,
)
from ..config import settings
from ..database import get_db
from ..models.role import Role as RoleModel

# Impor model dan skema secara langsung
from ..models.user import User as UserModel
from ..schemas.user import User as UserSchema
from ..schemas.user import UserCreate, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


# Endpoint /token tidak perlu diubah karena hanya untuk otentikasi
@router.post("/token", summary="Create access token for user")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    query = select(UserModel).where(UserModel.email == form_data.username)
    user = (await db.execute(query)).scalar_one_or_none()

    # --- PERIKSA BLOK INI DENGAN SEKSAMA ---
    if not user:
        # INI BAGIAN YANG PENTING
        # Kirim status 401 Unauthorized jika user tidak ditemukan/password salah
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # --- AKHIR BLOK PEMERIKSAAN ---

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Endpoint /me sekarang menggunakan dependency yang sudah eager loading
@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user),
):
    return current_user


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user_query = await db.execute(
        select(UserModel).where(UserModel.email == user.email)
    )
    if existing_user_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User dengan email '{user.email}' sudah ada.",
        )

    if user.role_id:
        role = await db.get(RoleModel, user.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role dengan id {user.role_id} tidak ditemukan.",
            )

    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_password

    db_user = UserModel(**user_data)
    db.add(db_user)
    await db.commit()

    # Ambil ulang data dengan relasi untuk respons
    query = (
        select(UserModel)
        .where(UserModel.id == db_user.id)
        .options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
    )
    created_user = (await db.execute(query)).scalar_one_or_none()

    return created_user


@router.get("/", response_model=List[UserSchema])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    # Gunakan eager loading untuk mengambil semua user beserta role-nya
    query = select(UserModel).options(
        selectinload(UserModel.role).selectinload(RoleModel.permissions)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    # Gunakan eager loading untuk mengambil satu user
    query = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
    )
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)
):
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password"] = get_password_hash(update_data["password"])
    elif "password" in update_data:
        del update_data["password"]  # Jangan update password jika kosong

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    await db.commit()

    # Ambil ulang data dengan relasi untuk respons
    query = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
    )
    updated_user = (await db.execute(query)).scalar_one_or_none()

    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(db_user)
    await db.commit()
    return None


# === Endpoint Baru untuk Forgot Password (Tanpa Email) ===
@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    query = select(UserModel).where(UserModel.email == email)
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User dengan email tersebut tidak ditemukan",
        )

    # Generate token reset (disimpan di user)
    reset_token = str(uuid.uuid4())
    reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Token berlaku 1 jam

    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires
    db.add(user)
    await db.commit()

    return {
        "message": "Silakan lanjutkan ke langkah reset password dengan token ini.",
        "token": reset_token,
    }


# === Endpoint Baru untuk Reset Password ===
@router.post("/reset-password")
async def reset_password(
    email: str, new_password: str, token: str, db: AsyncSession = Depends(get_db)
):
    query = select(UserModel).where(
        UserModel.email == email, UserModel.reset_token == token
    )
    user = (await db.execute(query)).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email atau token reset tidak valid",
        )

    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token reset telah kadaluarsa",
        )

    # Hash password baru
    hashed_password = get_password_hash(new_password)

    # Update password dan hapus token
    user.password = hashed_password
    user.reset_token = None
    user.reset_token_expires = None
    db.add(user)
    await db.commit()

    return {
        "message": "Password berhasil diatur ulang. Silakan login dengan password baru."
    }
