from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..schemas.paket_layanan import (
    PaketLayanan as PaketLayananSchema,
    PaketLayananCreate,
    PaketLayananUpdate,
)
from ..database import get_db

router = APIRouter(prefix="/paket_layanan", tags=["Paket Layanan"])


@router.post("/", response_model=PaketLayananSchema, status_code=status.HTTP_201_CREATED)
async def create_paket_layanan(paket: PaketLayananCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if id_brand exists in harga_layanan table
        from ..models.harga_layanan import HargaLayanan as HargaLayananModel

        harga_layanan_result = await db.execute(
            select(HargaLayananModel).where(HargaLayananModel.id_brand == paket.id_brand)
        )
        harga_layanan = harga_layanan_result.scalar_one_or_none()

        if not harga_layanan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand '{paket.id_brand}' tidak ditemukan. Silakan tambahkan brand terlebih dahulu."
            )

        db_paket = PaketLayananModel(**paket.model_dump())
        db.add(db_paket)
        await db.commit()
        await db.refresh(db_paket)

        return db_paket

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat paket layanan: {str(e)}"
        )


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
async def update_paket_layanan(paket_id: int, paket_update: PaketLayananUpdate, db: AsyncSession = Depends(get_db)):
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


@router.delete("/{paket_id}")
async def delete_paket_layanan(paket_id: int, db: AsyncSession = Depends(get_db)):
    db_paket = await db.get(PaketLayananModel, paket_id)
    if not db_paket:
        raise HTTPException(status_code=404, detail="Paket layanan tidak ditemukan")

    await db.delete(db_paket)
    await db.commit()
    return {"message": "Paket layanan berhasil dihapus"}