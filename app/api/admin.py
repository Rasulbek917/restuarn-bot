from datetime import datetime, time, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.banner import Banner
from app.models.category import Category
from app.models.order import Order
from app.models.product import Product
from app.models.review import Review
from app.models.staff import Staff
from app.models.user import User
from app.schemas.admin import (
    BannerCreate,
    BannerUpdate,
    CategoryCreate,
    CategoryUpdate,
    DashboardOut,
    ProductCreate,
    ProductUpdate,
    StaffCreate,
    StaffOut,
    StaffUpdate,
)
from app.schemas.catalog import BannerOut, CategoryOut, ProductOut
from app.schemas.orders import OrderOut
from app.utils.deps import require_role, require_staff_auth

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_staff_auth), Depends(require_role("ADMIN"))],
)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(db: AsyncSession = Depends(get_db)):
    start_of_day = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    today_orders_result = await db.execute(
        select(Order).where(Order.createdAt >= start_of_day, Order.status != "PENDING")
    )
    today_orders = today_orders_result.scalars().all()

    active_orders = (
        await db.execute(
            select(func.count()).select_from(Order).where(
                Order.status.in_(["CONFIRMED", "PREPARING", "READY", "DELIVERING"])
            )
        )
    ).scalar_one()

    completed_today = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.createdAt >= start_of_day, Order.status == "COMPLETED")
        )
    ).scalar_one()

    cancelled_today = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.createdAt >= start_of_day, Order.status.in_(["CANCELLED", "REJECTED"]))
        )
    ).scalar_one()

    avg_rating = (await db.execute(select(func.avg(Review.rating)))).scalar_one()

    today_sales = sum(o.total for o in today_orders if o.status.value == "COMPLETED")

    return DashboardOut(
        todayOrdersCount=len(today_orders),
        todaySales=today_sales,
        activeOrders=active_orders,
        completedToday=completed_today,
        cancelledToday=cancelled_today,
        averageRating=float(avg_rating) if avg_rating is not None else 0,
    )


# ---------------------------------------------------------------------------
# Orders (read)
# ---------------------------------------------------------------------------
@router.get("/orders", response_model=List[OrderOut])
async def admin_orders(status: Optional[str] = Query(default=None), db: AsyncSession = Depends(get_db)):
    stmt = select(Order).options(
        selectinload(Order.items), selectinload(Order.address), selectinload(Order.user)
    )
    if status:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.createdAt.desc()).limit(200)

    result = await db.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
@router.get("/products", response_model=List[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).order_by(Product.createdAt.desc())
    )
    return result.scalars().all()


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**body.model_dump(exclude_none=True))
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, body: ProductUpdate, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Topilmadi")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Topilmadi")
    await db.delete(product)
    await db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@router.get("/categories", response_model=List[CategoryOut])
async def admin_list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.order.asc()))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category = Category(**body.model_dump(exclude_none=True))
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(category_id: str, body: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Topilmadi")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Topilmadi")
    await db.delete(category)
    await db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------
@router.get("/banners", response_model=List[BannerOut])
async def admin_list_banners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Banner).order_by(Banner.order.asc()))
    return result.scalars().all()


@router.post("/banners", response_model=BannerOut, status_code=201)
async def create_banner(body: BannerCreate, db: AsyncSession = Depends(get_db)):
    banner = Banner(**body.model_dump(exclude_none=True))
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.patch("/banners/{banner_id}", response_model=BannerOut)
async def update_banner(banner_id: str, body: BannerUpdate, db: AsyncSession = Depends(get_db)):
    banner = await db.get(Banner, banner_id)
    if not banner:
        raise HTTPException(404, "Topilmadi")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(banner, key, value)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.delete("/banners/{banner_id}", status_code=204)
async def delete_banner(banner_id: str, db: AsyncSession = Depends(get_db)):
    banner = await db.get(Banner, banner_id)
    if not banner:
        raise HTTPException(404, "Topilmadi")
    await db.delete(banner)
    await db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Reviews (read)
# ---------------------------------------------------------------------------
@router.get("/reviews")
async def list_reviews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).options(selectinload(Review.user), selectinload(Review.order)).order_by(Review.createdAt.desc())
    )
    reviews = result.scalars().all()
    return [
        {
            "id": r.id,
            "orderId": r.orderId,
            "userId": r.userId,
            "rating": r.rating,
            "comment": r.comment,
            "createdAt": r.createdAt,
            "user": {"id": r.user.id, "firstName": r.user.firstName, "lastName": r.user.lastName} if r.user else None,
            "order": {"id": r.order.id, "orderNumber": r.order.orderNumber} if r.order else None,
        }
        for r in reviews
    ]


# ---------------------------------------------------------------------------
# Users (read)
# ---------------------------------------------------------------------------
@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User, func.count(Order.id).label("orderCount"))
        .outerjoin(Order, Order.userId == User.id)
        .group_by(User.id)
        .order_by(User.createdAt.desc())
        .limit(500)
    )
    rows = result.all()
    return [
        {
            "id": u.id,
            "telegramId": u.telegramId,
            "firstName": u.firstName,
            "lastName": u.lastName,
            "phone": u.phone,
            "username": u.username,
            "languageCode": u.languageCode,
            "createdAt": u.createdAt,
            "_count": {"orders": count},
        }
        for u, count in rows
    ]


# ---------------------------------------------------------------------------
# Staff management
# ---------------------------------------------------------------------------
@router.get("/staff", response_model=List[StaffOut])
async def list_staff(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff))
    return result.scalars().all()


@router.post("/staff", response_model=StaffOut, status_code=201)
async def create_staff(body: StaffCreate, db: AsyncSession = Depends(get_db)):
    staff = Staff(**body.model_dump())
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff


@router.patch("/staff/{staff_id}", response_model=StaffOut)
async def update_staff(staff_id: str, body: StaffUpdate, db: AsyncSession = Depends(get_db)):
    staff = await db.get(Staff, staff_id)
    if not staff:
        raise HTTPException(404, "Topilmadi")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(staff, key, value)
    await db.commit()
    await db.refresh(staff)
    return staff
