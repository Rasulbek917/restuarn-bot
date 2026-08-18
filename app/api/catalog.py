from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.banner import Banner
from app.models.category import Category
from app.models.product import Product
from app.schemas.catalog import BannerOut, CategoryOut, ProductOut

# TS versiyada `app.use("/api", catalogRouter)` bilan mount qilingan — shu bilan
# frontend'dagi mavjud /api/categories, /api/banners, /api/products yo'llari saqlanadi.
router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.isActive.is_(True)).order_by(Category.order.asc()))
    return result.scalars().all()


@router.get("/banners", response_model=List[BannerOut])
async def list_banners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Banner).where(Banner.isActive.is_(True)).order_by(Banner.order.asc()))
    return result.scalars().all()


@router.get("/products", response_model=List[ProductOut])
async def list_products(
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Real-time qidiruv: ?category=<id>&search=<text>"""
    stmt = select(Product).where(Product.isAvailable.is_(True))
    if category and category != "ALL":
        stmt = stmt.where(Product.categoryId == category)
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(Product.createdAt.asc())

    result = await db.execute(stmt)
    return result.scalars().all()
