# app/routers/role.py
"""
Role Management Router - CRUD operations untuk role-based access control

Router ini handle semua role management operations di sistem billing.
Role adalah kumpulan permissions yang bisa diassign ke users.

Role-Based Access Control (RBAC):
- User -> Role -> Permission
- Multiple users bisa punya role yang sama
- Role bisa punya multiple permissions
- Flexible dan scalable permission system

Role Structure:
- Role name: Unique identifier (admin, finance, support, dll)
- Permissions: List of permission IDs
- Users: List of users assigned to role

Common Role Examples:
- admin: Full system access
- finance: Billing, invoice, and financial reports
- support: Customer data and trouble tickets
- teknisi: Network monitoring and technical data
- operator: Basic operational access

Security Features:
- Unique role names (no duplicates)
- Permission assignment validation
- Efficient eager loading (prevent N+1 queries)
- Atomic database operations

Integration Points:
- Permission management system
- User management and assignment
- Authorization decorators (@has_permission)
- Frontend access control

Usage Flow:
1. Create role dengan specific permissions
2. Assign role ke users
3. Users inherit all role permissions
4. Check permissions di protected endpoints
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # Penting untuk eager loading
from typing import List

# Impor model dan skema yang relevan
from ..models.role import Role as RoleModel
from ..models.permission import Permission as PermissionModel
from ..schemas.role import Role as RoleSchema, RoleCreate, RoleUpdate
from ..database import get_db

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: AsyncSession = Depends(get_db)):
    """
    Create New Role - Buat role baru dengan permissions

    Function ini buat role baru dan assign permissions ke role tersebut.
    Role adalah container buat permissions yang bisa diassign ke users.

    Role Creation Process:
    1. Validate role name uniqueness
    2. Create role entity dengan name
    3. Assign permissions kalau ada
    4. Save ke database dengan atomic operation
    5. Return complete role dengan permissions loaded

    Validation Features:
    - Unique role name checking (prevent duplicates)
    - Permission existence validation
    - Proper HTTP status codes
    - Comprehensive error messages

    Permission Assignment:
    - Optional: role bisa dibuat tanpa permissions
    - Validation: hanya existing permissions yang diassign
    - Many-to-many relationship handling
    - Efficient bulk assignment

    Database Operations:
    - Atomic transaction (commit atau rollback)
    - Eager loading untuk complete response
    - Efficient permission lookup dengan IN clause
    - Proper relationship management

    Security Features:
    - Input validation dan sanitization
    - SQL injection prevention via SQLAlchemy
    - Permission existence checking
    - Consistent error handling

    Args:
        role_data: RoleCreate schema dengan name dan permission_ids
        db: AsyncSession database connection

    Returns:
        RoleSchema: Complete role yang baru dibuat dengan permissions

    Raises:
        HTTPException 409: Role name already exists
    """

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
