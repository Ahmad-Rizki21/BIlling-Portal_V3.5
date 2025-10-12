from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # Penting untuk eager loading

from ..database import get_db
from ..models.permission import Permission as PermissionModel

# Impor model dan skema yang relevan
from ..models.role import Role as RoleModel
from ..schemas.role import Role as RoleSchema
from ..schemas.role import RoleCreate, RoleUpdate

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: AsyncSession = Depends(get_db)):

    # --- TAMBAHKAN BLOK PENGECEKAN INI ---
    # Cek apakah role dengan nama yang sama sudah ada
    existing_role_query = await db.execute(select(RoleModel).where(RoleModel.name == role_data.name))
    if existing_role_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role dengan nama '{role_data.name}' sudah ada.",
        )
    # ------------------------------------

    db_role = RoleModel(name=role_data.name)

    if role_data.permission_ids:
        permissions = await db.execute(select(PermissionModel).where(PermissionModel.id.in_(role_data.permission_ids)))
        db_role.permissions.extend(permissions.scalars().all())

    db.add(db_role)
    await db.commit()
    role_id = db_role.id

    # --- KUNCI PERBAIKAN ADA DI SINI ---
    # Setelah commit, ambil ulang datanya dengan eager loading
    # sebelum dikembalikan sebagai respons.
    query = select(RoleModel).where(RoleModel.id == role_id).options(selectinload(RoleModel.permissions))
    result = await db.execute(query)
    created_role = result.scalar_one_or_none()

    return created_role


@router.get("/", response_model=List[RoleSchema])
async def get_all_roles(db: AsyncSession = Depends(get_db)):
    # Gunakan selectinload untuk memuat permissions bersamaan (menghindari N+1 query)
    result = await db.execute(select(RoleModel).options(selectinload(RoleModel.permissions)))
    return result.scalars().all()


@router.patch("/{role_id}", response_model=RoleSchema)
async def update_role(role_id: int, role_update: RoleUpdate, db: AsyncSession = Depends(get_db)):
    # Ambil role beserta permissions-nya
    db_role = (
        await db.execute(select(RoleModel).options(selectinload(RoleModel.permissions)).where(RoleModel.id == role_id))
    ).scalar_one_or_none()

    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Update nama jika ada
    if role_update.name:
        db_role.name = role_update.name

    # Update permissions jika ada (termasuk jika dikirim list kosong)
    if role_update.permission_ids is not None:
        query = select(PermissionModel).where(PermissionModel.id.in_(role_update.permission_ids))
        permissions = (await db.execute(query)).scalars().all()
        db_role.permissions = permissions  # Ganti semua permission dengan yang baru  # type: ignore

    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    db_role = await db.get(RoleModel, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    await db.delete(db_role)
    await db.commit()
    return None
