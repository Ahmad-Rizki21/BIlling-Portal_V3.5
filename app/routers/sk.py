# app/routers/sk.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..models.sk import SK as SKModel
from ..schemas.sk import SK as SKSchema, SKCreate, SKUpdate
from ..database import get_db

router = APIRouter(prefix="/sk", tags=["S&K"])


@router.post("/", response_model=SKSchema, status_code=status.HTTP_201_CREATED)
async def create_sk(sk_data: SKCreate, db: AsyncSession = Depends(get_db)):
    db_sk = SKModel(**sk_data.model_dump())
    db.add(db_sk)
    await db.commit()
    await db.refresh(db_sk)
    return db_sk


@router.get("/", response_model=List[SKSchema])
async def get_all_sk(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SKModel).order_by(SKModel.created_at.desc()))
    return result.scalars().all()


# ===== TAMBAHAN BARU =====
@router.patch("/{sk_id}", response_model=SKSchema)
async def update_sk(sk_id: int, sk_data: SKUpdate, db: AsyncSession = Depends(get_db)):
    db_sk = await db.get(SKModel, sk_id)
    if not db_sk:
        raise HTTPException(status_code=404, detail="Item S&K tidak ditemukan")

    update_data = sk_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sk, key, value)

    db.add(db_sk)
    await db.commit()
    await db.refresh(db_sk)
    return db_sk


@router.delete("/{sk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sk(sk_id: int, db: AsyncSession = Depends(get_db)):
    db_sk = await db.get(SKModel, sk_id)
    if not db_sk:
        raise HTTPException(status_code=404, detail="Item S&K tidak ditemukan")

    await db.delete(db_sk)
    await db.commit()
    return None


# ========================
