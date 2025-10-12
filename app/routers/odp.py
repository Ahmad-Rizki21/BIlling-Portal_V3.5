from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.odp import ODP as ODPModel
from ..schemas.odp import ODP as ODPSchema
from ..schemas.odp import ODPCreate, ODPUpdate

router = APIRouter(prefix="/odp", tags=["ODP"])


@router.post("/", response_model=ODPSchema, status_code=status.HTTP_201_CREATED)
async def create_odp(odp_data: ODPCreate, db: AsyncSession = Depends(get_db)):
    db_odp = ODPModel(**odp_data.model_dump())
    db.add(db_odp)
    await db.commit()
    await db.refresh(db_odp, attribute_names=["olt", "parent_odp"])  # <-- PERUBAHAN

    # Buat respons manual untuk menyertakan port_terpakai=0
    response_odp = ODPSchema.from_orm(db_odp)
    response_odp.port_terpakai = 0
    return response_odp


@router.get("/", response_model=List[ODPSchema])
async def get_all_odps(db: AsyncSession = Depends(get_db)):
    # Subquery untuk menghitung port terpakai tetap sama
    subquery = (
        select(
            DataTeknisModel.odp_id,
            func.count(DataTeknisModel.id).label("jumlah_terpakai"),
        )
        .where(DataTeknisModel.odp_id.isnot(None))
        .group_by(DataTeknisModel.odp_id)
        .subquery()
    )

    query = (
        select(ODPModel, func.coalesce(subquery.c.jumlah_terpakai, 0)).outerjoin(subquery, ODPModel.id == subquery.c.odp_id)
        # --- ▼▼▼ PERUBAHAN DI SINI ▼▼▼ ---
        # Eager load relasi 'olt' dan 'parent_odp' dalam satu query
        .options(selectinload(ODPModel.olt), selectinload(ODPModel.parent_odp))
        # --- ▲▲▲ AKHIR PERUBAHAN ▲▲▲ ---
        .order_by(ODPModel.kode_odp)
    )

    result = await db.execute(query)
    odp_list = []
    for odp, port_terpakai in result.all():
        odp_schema = ODPSchema.from_orm(odp)
        odp_schema.port_terpakai = port_terpakai
        odp_list.append(odp_schema)

    return odp_list


# Anda bisa menambahkan endpoint GET by ID, PATCH, dan DELETE di sini
# dengan mencontoh dari file app/routers/olt.py


@router.get("/{odp_id}", response_model=ODPSchema)
async def get_odp_by_id(odp_id: int, db: AsyncSession = Depends(get_db)):
    # Query ini dibuat lebih efisien untuk mengambil semua data sekaligus
    subquery = select(func.count(DataTeknisModel.id)).where(DataTeknisModel.odp_id == odp_id).scalar_subquery()

    query = (
        select(ODPModel, func.coalesce(subquery, 0)).filter(ODPModel.id == odp_id)
        # --- ▼▼▼ PERUBAHAN DI SINI ▼▼▼ ---
        .options(selectinload(ODPModel.olt), selectinload(ODPModel.parent_odp))
        # --- ▲▲▲ AKHIR PERUBAHAN ▲▲▲ ---
    )

    result = await db.execute(query)
    record = result.one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="ODP not found")

    odp, port_terpakai = record
    response_odp = ODPSchema.from_orm(odp)
    response_odp.port_terpakai = port_terpakai
    return response_odp


@router.patch("/{odp_id}", response_model=ODPSchema)
async def update_odp(odp_id: int, odp_data: ODPUpdate, db: AsyncSession = Depends(get_db)):
    db_odp = await db.get(ODPModel, odp_id)
    if not db_odp:
        raise HTTPException(status_code=404, detail="ODP not found")

    update_data = odp_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_odp, key, value)

    db.add(db_odp)
    await db.commit()

    # Panggil get_odp_by_id yang sudah diperbarui untuk mendapatkan respons yang lengkap
    return await get_odp_by_id(odp_id, db)


@router.delete("/{odp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_odp(odp_id: int, db: AsyncSession = Depends(get_db)):
    db_odp = await db.get(ODPModel, odp_id)
    if not db_odp:
        raise HTTPException(status_code=404, detail="ODP not found")

    result = await db.execute(select(func.count(DataTeknisModel.id)).where(DataTeknisModel.odp_id == odp_id))
    if result.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ODP tidak dapat dihapus karena masih terhubung dengan data teknis pelanggan.",
        )

    await db.delete(db_odp)
    await db.commit()
    return None
