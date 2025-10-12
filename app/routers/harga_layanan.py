from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..schemas.harga_layanan import (
    HargaLayanan as HargaLayananSchema,
    HargaLayananCreate,
    HargaLayananUpdate,
)
from ..database import get_db
from ..services.cache_service import get_cached_harga_layanan, invalidate_data_caches

router = APIRouter(prefix="/harga_layanan", tags=["Harga Layanan (Brand)"])


@router.post("/", response_model=HargaLayananSchema, status_code=status.HTTP_201_CREATED)
async def create_brand(brand_data: HargaLayananCreate, db: AsyncSession = Depends(get_db)):
    db_brand = HargaLayananModel(**brand_data.model_dump())
    db.add(db_brand)
    await db.commit()
    await db.refresh(db_brand)

    # Cache Strategy: Invalidate cache saat ada perubahan data
    invalidate_data_caches()

    return db_brand


@router.get("/", response_model=List[HargaLayananSchema])
async def get_all_brands(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Get all harga layanan dengan caching.
    Cache Strategy: Static data di-cache selama 1 jam untuk mengurangi database load.
    """
    # Add cache headers untuk browser cache
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 menit browser cache

    # Try to get from cache first
    try:
        cached_data = await get_cached_harga_layanan(db)
        if cached_data:
            # Add cache headers untuk indikasi cache hit
            response.headers["X-Cache"] = "HIT"
            from ..services.cache_service import CACHE_CONFIG

            response.headers["X-Cache-TTL"] = str(CACHE_CONFIG["harga_layanan_ttl"])

            # Convert cached dict back to model objects
            return [HargaLayananSchema(**item) for item in cached_data]
    except Exception as e:
        # Fallback to database query if cache fails
        print(f"Cache error, falling back to database: {e}")

    # Fallback database query
    response.headers["X-Cache"] = "MISS"
    result = await db.execute(select(HargaLayananModel))
    return result.scalars().all()


@router.get("/{id_brand}", response_model=HargaLayananSchema)
async def get_brand_by_id(id_brand: str, db: AsyncSession = Depends(get_db)):
    brand = await db.get(HargaLayananModel, id_brand)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")
    return brand


@router.patch("/{id_brand}", response_model=HargaLayananSchema)
async def update_brand(id_brand: str, brand_update: HargaLayananUpdate, db: AsyncSession = Depends(get_db)):
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
