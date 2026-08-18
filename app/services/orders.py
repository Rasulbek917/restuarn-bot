from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus, StaffRole
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.product import Product
from app.services.notify import notify_customer_status, post_order_to_group, update_group_order_card


class OrderError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _order_query():
    return select(Order).options(
        selectinload(Order.items),
        selectinload(Order.address),
        selectinload(Order.user),
    )


async def get_full_order(db: AsyncSession, order_id: str) -> Order | None:
    result = await db.execute(_order_query().where(Order.id == order_id))
    return result.scalar_one_or_none()


async def create_order_from_cart(db: AsyncSession, user_id: str, items: List[Tuple[str, int]]) -> Order:
    """
    Savatdan order yaratadi. Narxlarni HECH QACHON clientdan olmaymiz —
    har bir productId uchun DB'dan joriy narxni o'qib, shu yerda hisoblaymiz
    (server-side price calculation, client narxiga ishonmaslik).
    """
    if not items:
        raise OrderError("Savat bo'sh")

    product_ids = [pid for pid, _ in items]
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products: Dict[str, Product] = {p.id: p for p in result.scalars().all()}

    total = 0
    order_items: List[OrderItem] = []
    for product_id, quantity in items:
        product = products.get(product_id)
        if not product or not product.isAvailable:
            raise OrderError(f"Mahsulot mavjud emas: {product_id}")
        if quantity < 1 or quantity > 50:
            raise OrderError("Noto'g'ri miqdor")
        total += product.price * quantity
        order_items.append(
            OrderItem(productId=product.id, name=product.name, price=product.price, quantity=quantity)
        )

    order = Order(userId=user_id, status=OrderStatus.PENDING, total=total, items=order_items)
    db.add(order)
    await db.commit()

    return await get_full_order(db, order.id)


async def finalize_order(db: AsyncSession, order_id: str, user_id: str) -> Order:
    """Mijoz final \"TASDIQLASH\" bosganda — order to'liqligini tekshirib, guruhga yuboradi."""
    order = await get_full_order(db, order_id)
    if not order or order.userId != user_id:
        raise OrderError("Order topilmadi", 404)
    if order.status != OrderStatus.PENDING:
        raise OrderError("Order allaqachon yuborilgan")
    if not order.paymentMethod:
        raise OrderError("To'lov usuli tanlanmagan")
    if order.paymentMethod.value == "CARD" and order.paymentStatus.value != "PAID":
        raise OrderError("To'lov hali tasdiqlanmagan")
    if not order.addressId:
        raise OrderError("Manzil kiritilmagan")
    if not order.phone or not order.firstName or not order.lastName:
        raise OrderError("Foydalanuvchi ma'lumotlari to'liq emas")

    message_id = await post_order_to_group(order)
    order.groupMessageId = message_id
    db.add(OrderStatusHistory(orderId=order.id, status=OrderStatus.PENDING))
    await db.commit()

    return await get_full_order(db, order.id)


async def cancel_order(db: AsyncSession, order_id: str, user_id: str) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise OrderError("Order topilmadi", 404)
    if order.status != OrderStatus.PENDING:
        raise OrderError("Bu bosqichda buyurtmani bekor qilib bo'lmaydi")

    order.status = OrderStatus.CANCELLED
    await db.commit()
    return await get_full_order(db, order_id)


# Qat'iy status tartibi — har bir role faqat o'z bosqichini o'zgartira oladi.
ALLOWED_TRANSITIONS: Dict[str, Dict] = {
    "accept": {"from": OrderStatus.PENDING, "to": OrderStatus.CONFIRMED, "roles": [StaffRole.ADMIN]},
    "reject": {"from": OrderStatus.PENDING, "to": OrderStatus.REJECTED, "roles": [StaffRole.ADMIN]},
    "preparing": {"from": OrderStatus.CONFIRMED, "to": OrderStatus.PREPARING, "roles": [StaffRole.ADMIN, StaffRole.COOK]},
    "ready": {"from": OrderStatus.PREPARING, "to": OrderStatus.READY, "roles": [StaffRole.ADMIN, StaffRole.COOK]},
    "delivering": {"from": OrderStatus.READY, "to": OrderStatus.DELIVERING, "roles": [StaffRole.ADMIN, StaffRole.COURIER]},
    "complete": {"from": OrderStatus.DELIVERING, "to": OrderStatus.COMPLETED, "roles": [StaffRole.ADMIN, StaffRole.COURIER]},
}


async def transition_order_status(db: AsyncSession, order_id: str, action: str, staff_id: str, staff_role: StaffRole) -> Order:
    rule = ALLOWED_TRANSITIONS.get(action)
    if not rule:
        raise OrderError("Noma'lum amal")
    if staff_role not in rule["roles"]:
        raise OrderError("Sizga bu amal uchun ruxsat yo'q", 403)

    order = await get_full_order(db, order_id)
    if not order:
        raise OrderError("Order topilmadi", 404)
    if order.status != rule["from"]:
        raise OrderError(f"Order holati \"{rule['from'].value}\" bo'lishi kerak edi, hozir \"{order.status.value}\"")

    order.status = rule["to"]
    db.add(OrderStatusHistory(orderId=order_id, status=rule["to"], staffId=staff_id))
    await db.commit()

    updated = await get_full_order(db, order_id)
    await update_group_order_card(updated)
    await notify_customer_status(updated)

    return updated
