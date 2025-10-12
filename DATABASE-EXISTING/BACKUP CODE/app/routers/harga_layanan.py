from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..schemas.harga_layanan import HargaLayanan as HargaLayananSchema
from ..schemas.harga_layanan import (
    HargaLayananCreate,
    HargaLayananUpdate,
)

router = APIRouter(prefix="/harga_layanan", tags=["Harga Layanan (Brand)"])


@router.post(
    "/", response_model=HargaLayananSchema, status_code=status.HTTP_201_CREATED
)
async def create_brand(
    brand_data: HargaLayananCreate, db: AsyncSession = Depends(get_db)
):
    db_brand = HargaLayananModel(**brand_data.model_dump())
    db.add(db_brand)
    await db.commit()
    await db.refresh(db_brand)
    return db_brand


@router.get("/", response_model=List[HargaLayananSchema])
async def get_all_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HargaLayananModel))
    return result.scalars().all()


@router.get("/{id_brand}", response_model=HargaLayananSchema)
async def get_brand_by_id(id_brand: str, db: AsyncSession = Depends(get_db)):
    brand = await db.get(HargaLayananModel, id_brand)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")
    return brand


@router.patch("/{id_brand}", response_model=HargaLayananSchema)
async def update_brand(
    id_brand: str, brand_update: HargaLayananUpdate, db: AsyncSession = Depends(get_db)
):
    db_brand = await db.get(HargaLayananModel, id_brand)
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")

    update_data = brand_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_brand, key, value)

    db.add(db_brand)
    await db.commit()
    await db.refresh(db_brand)
    return db_brand


@router.delete("/{id_brand}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(id_brand: str, db: AsyncSession = Depends(get_db)):
    db_brand = await db.get(HargaLayananModel, id_brand)
    if not db_brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")

    await db.delete(db_brand)
    await db.commit()
    return None
