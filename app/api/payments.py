import hashlib
import hmac
import json
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.order import Order, Payment
from app.utils.deps import require_customer_auth

router = APIRouter(prefix="/api/payments", tags=["payments"])

"""
KARTADAN TO'LASH oqimi.

Bu yerda O'zbekiston bozorida keng tarqalgan Click/Payme kabi providerlar uchun
umumiy struktura keltirilgan. Aniq provider PAYMENT_PROVIDER env orqali tanlanadi,
shunda kod o'zgarmasdan provider almashtirilishi mumkin.

PRODUCTIONGA CHIQISHDAN OLDIN:
 - Tanlangan provayderning rasmiy SDK/checkout URL formatini shu joyga ulang
 - Webhook signature tekshiruvini provayderning real algoritmiga moslang
 - TODO'larni tanlangan provider hujjatiga qarab to'ldiring
"""


class CardInitRequest(BaseModel):
    orderId: str


class CardInitResponse(BaseModel):
    paymentId: str
    checkoutUrl: str


@router.post("/card/init", response_model=CardInitResponse)
async def card_init(
    body: CardInitRequest, user_id: str = Depends(require_customer_auth), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == body.orderId))
    order = result.scalar_one_or_none()
    if not order or order.userId != user_id:
        raise HTTPException(404, "Topilmadi")
    if not order.paymentMethod or order.paymentMethod.value != "CARD":
        raise HTTPException(400, "To'lov usuli CARD emas")

    payment = Payment(orderId=order.id, provider=settings.PAYMENT_PROVIDER, amount=order.total, status="PENDING")
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # TODO: haqiqiy provider checkout sessiyasini shu yerda oching va
    # foydalanuvchini shu URLga (yoki Telegram Invoice'ga) yo'naltiring.
    checkout_url = (
        f"https://payment.example.com/checkout?ref={payment.id}"
        f"&amount={order.total}&provider={settings.PAYMENT_PROVIDER}"
    )
    return CardInitResponse(paymentId=payment.id, checkoutUrl=checkout_url)


class WebhookBody(BaseModel):
    paymentId: str
    status: Literal["PAID", "FAILED"]


@router.post("/webhook")
async def payment_webhook(
    body: WebhookBody,
    x_signature: str | None = Header(default=None, alias="x-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Provider webhook — to'lov holatini yangilaydi. Faqat PAID bo'lgandan keyin
    order keyingi bosqichga o'tadi. Signature tekshiruvi HMAC bilan ko'rsatilgan —
    real providerning aniq algoritmiga moslab almashtiring."""
    payload_bytes = json.dumps(body.model_dump()).encode()
    expected = hmac.new(
        (settings.PAYMENT_WEBHOOK_SECRET or "unset").encode(), payload_bytes, hashlib.sha256
    ).hexdigest()

    if not settings.PAYMENT_WEBHOOK_SECRET or not x_signature or not hmac.compare_digest(x_signature, expected):
        raise HTTPException(401, "Invalid webhook signature")

    payment = await db.get(Payment, body.paymentId)
    if not payment:
        raise HTTPException(404, "Payment topilmadi")

    payment.status = body.status
    order = await db.get(Order, payment.orderId)
    if order:
        order.paymentStatus = body.status

    await db.commit()
    return {"ok": True}
