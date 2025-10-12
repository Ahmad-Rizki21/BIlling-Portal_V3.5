from operator import or_
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # <-- Pastikan diimpor
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordRequestForm

# Impor model dan skema secara langsung
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..schemas.user import User as UserSchema, UserCreate, UserUpdate
from ..database import get_db
from ..auth import (
    get_current_active_user,
    get_password_hash,
    verify_password,
)  # <-- Impor get_password_hash dan verify_password dari auth
from .. import auth
from ..config import settings

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


# Endpoint /me sekarang menggunakan dependency yang sudah eager loading
@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user),
):
    return current_user


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create user dengan password validation untuk security.
    ✅ PASSWORD SECURE: Hanya password kuat yang diterima.
    """
    # 1. Check existing email
    existing_user_query = await db.execute(select(UserModel).where(UserModel.email == user.email))
    if existing_user_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User dengan email '{user.email}' sudah ada.",
        )

    # 2. Validate password strength BEFORE hashing
    from ..auth import validate_password_strength

    is_valid, errors = validate_password_strength(user.password)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Password tidak memenuhi keamanan requirements",
                "requirements": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_digit": True,
                    "require_special": True,
                    "no_whitespace": True,
                },
                "errors": errors,
            },
        )

    # 3. Hash password (only if validation passes)
    user_data = user.model_dump()
    role_id = user_data.pop("role_id", None)
    hashed_password = get_password_hash(user.password)
    user_data["password"] = hashed_password
    # Set password_changed_at to current time when creating user
    user_data["password_changed_at"] = datetime.utcnow()

    # 4. Create user record
    db_user = UserModel(**user_data)
    if role_id:
        db_user.role_id = role_id
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
async def read_all_users(
    skip: int = 0,
    limit: Optional[int] = 15,  # Default limit 15 items
    search: Optional[str] = None,
    role_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua user dengan paginasi dan filter.
    """
    query = select(UserModel).options(selectinload(UserModel.role).selectinload(RoleModel.permissions))

    # Terapkan filter pencarian (nama, email)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                UserModel.name.ilike(search_term),
                UserModel.email.ilike(search_term),
            )
        )

    # Terapkan filter berdasarkan role
    if role_id:
        query = query.where(UserModel.role_id == role_id)

    # Terapkan paginasi setelah semua filter
    if limit is not None:
        query = query.offset(skip).limit(limit)

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
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)

    # Handle role_id separately to manage the relationship
    if "role_id" in update_data:
        role_id = update_data.pop("role_id")
        if role_id is not None:
            role = await db.get(RoleModel, role_id)
            if not role:
                raise HTTPException(status_code=404, detail=f"Role dengan id {role_id} tidak ditemukan.")
            db_user.role = role
        else:
            db_user.role = None

    if "password" in update_data and update_data["password"]:
        # 🔒 Validate password strength BEFORE hashing
        from ..auth import validate_password_strength

        is_valid, errors = validate_password_strength(update_data["password"])

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Password baru tidak memenuhi keamanan requirements",
                    "requirements": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_digit": True,
                        "require_special": True,
                        "no_whitespace": True,
                    },
                    "errors": errors,
                },
            )

        # Only hash if validation passes
        update_data["password"] = get_password_hash(update_data["password"])
        # Update password_changed_at when password is changed
        update_data["password_changed_at"] = datetime.utcnow()
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
async def reset_password(email: str, new_password: str, token: str, db: AsyncSession = Depends(get_db)):
    query = select(UserModel).where(UserModel.email == email, UserModel.reset_token == token)
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
    # Update password_changed_at timestamp
    user.password_changed_at = datetime.utcnow()
    db.add(user)
    await db.commit()

    return {"message": "Password berhasil diatur ulang. Silakan login dengan password baru."}
