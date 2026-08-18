from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order
from app.models.review import Review
from app.models.user import Address, User
from app.schemas.orders import (
    AddressRequest,
    ContactRequest,
    CreateOrderRequest,
    OrderOut,
    PaymentMethodRequest,
    ReviewOut,
    ReviewRequest,
)
from app.services.orders import (
    OrderError,
    cancel_order,
    create_order_from_cart,
    finalize_order,
    get_full_order,
)
from app.utils.deps import require_customer_auth

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _raise_order_error(err: OrderError):
    raise HTTPException(status_code=err.status, detail=err.message)


@router.post("", response_model=OrderOut, status_code=201)
@router.post("/", response_model=OrderOut, status_code=201, include_in_schema=False)
async def create_order(
    body: CreateOrderRequest, user_id: str = Depends(require_customer_auth), db: AsyncSession = Depends(get_db)
):
    try:
        items = [(i.productId, i.quantity) for i in body.items]
        return await create_order_from_cart(db, user_id, items)
    except OrderError as err:
        _raise_order_error(err)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, user_id: str = Depends(require_customer_auth), db: AsyncSession = Depends(get_db)):
    order = await get_full_order(db, order_id)
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")
    return order


@router.post("/{order_id}/payment-method", response_model=OrderOut)
async def set_payment_method(
    order_id: str,
    body: PaymentMethodRequest,
    user_id: str = Depends(require_customer_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")

    order.paymentMethod = body.method
    order.paymentStatus = "NOT_REQUIRED" if body.method == "CASH" else "PENDING"
    await db.commit()
    return await get_full_order(db, order_id)


@router.post("/{order_id}/address", response_model=OrderOut)
async def set_address(
    order_id: str,
    body: AddressRequest,
    user_id: str = Depends(require_customer_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")

    address = Address(userId=user_id, latitude=body.latitude, longitude=body.longitude, rawText=body.rawText)
    db.add(address)
    await db.flush()
    order.addressId = address.id
    await db.commit()
    return await get_full_order(db, order_id)


@router.post("/{order_id}/contact", response_model=OrderOut)
async def set_contact(
    order_id: str,
    body: ContactRequest,
    user_id: str = Depends(require_customer_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")

    order.phone = body.phone
    order.firstName = body.firstName
    order.lastName = body.lastName

    # Telefon raqamini foydalanuvchi profiliga ham saqlaymiz
    user = await db.get(User, user_id)
    if user:
        user.phone = body.phone

    await db.commit()
    return await get_full_order(db, order_id)


@router.post("/{order_id}/confirm", response_model=OrderOut)
async def confirm_order(order_id: str, user_id: str = Depends(require_customer_auth), db: AsyncSession = Depends(get_db)):
    try:
        return await finalize_order(db, order_id, user_id)
    except OrderError as err:
        _raise_order_error(err)


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order_endpoint(order_id: str, user_id: str = Depends(require_customer_auth), db: AsyncSession = Depends(get_db)):
    try:
        return await cancel_order(db, order_id, user_id)
    except OrderError as err:
        _raise_order_error(err)


@router.post("/{order_id}/review", response_model=ReviewOut)
async def submit_review(
    order_id: str,
    body: ReviewRequest,
    user_id: str = Depends(require_customer_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")
    if order.status.value != "COMPLETED":
        raise HTTPException(400, "Order hali yakunlanmagan")

    existing = (await db.execute(select(Review).where(Review.orderId == order_id))).scalar_one_or_none()
    if existing:
        existing.rating = body.rating
        existing.comment = body.comment
        review = existing
    else:
        review = Review(orderId=order_id, userId=user_id, rating=body.rating, comment=body.comment)
        db.add(review)

    await db.commit()
    await db.refresh(review)
    return review
