from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..schemas.paket_layanan import PaketLayanan as PaketLayananSchema
from ..schemas.paket_layanan import (
    PaketLayananCreate,
    PaketLayananUpdate,
)

router = APIRouter(prefix="/paket_layanan", tags=["Paket Layanan"])


@router.post(
    "/", response_model=PaketLayananSchema, status_code=status.HTTP_201_CREATED
)
async def create_paket_layanan(
    paket: PaketLayananCreate, db: AsyncSession = Depends(get_db)
):
    db_paket = PaketLayananModel(**paket.model_dump())
    db.add(db_paket)
    await db.commit()
    await db.refresh(db_paket)
    return db_paket


@router.get("/", response_model=List[PaketLayananSchema])
async def get_all_paket_layanan(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaketLayananModel))
    return result.scalars().all()


@router.get("/{paket_id}", response_model=PaketLayananSchema)
async def get_paket_layanan_by_id(paket_id: int, db: AsyncSession = Depends(get_db)):
    paket = await db.get(PaketLayananModel, paket_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket layanan tidak ditemukan")
    return paket


@router.patch("/{paket_id}", response_model=PaketLayananSchema)
async def update_paket_layanan(
    paket_id: int, paket_update: PaketLayananUpdate, db: AsyncSession = Depends(get_db)
):
    db_paket = await db.get(PaketLayananModel, paket_id)
    if not db_paket:
        raise HTTPException(status_code=404, detail="Paket layanan tidak ditemukan")

    update_data = paket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_paket, key, value)

    db.add(db_paket)
    await db.commit()
    await db.refresh(db_paket)
    return db_paket


@router.delete("/{paket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paket_layanan(paket_id: int, db: AsyncSession = Depends(get_db)):
    db_paket = await db.get(PaketLayananModel, paket_id)
    if not db_paket:
        raise HTTPException(status_code=404, detail="Paket layanan tidak ditemukan")

    await db.delete(db_paket)
    await db.commit()
    return None
