from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.bot.bot import bot
from app.bot.keyboards import keyboard_for_status
from app.config import settings
from app.models.order import Order

PAYMENT_LABELS = {
    "CASH": "Qabul qilganda",
    "CARD": "Karta orqali (online)",
}


def _payment_label(method: str | None) -> str:
    return PAYMENT_LABELS.get(method, "—")


def _format_items(order: Order) -> str:
    lines = [f"🍔 {i.name} × {i.quantity} — {i.price * i.quantity:,} so'm".replace(",", " ") for i in order.items]
    return "\n".join(lines)


def _location_line(order: Order) -> str:
    if not order.address:
        return "—"
    return f"https://maps.google.com/?q={order.address.latitude},{order.address.longitude}"


def _order_card_text(order: Order) -> str:
    """Guruhga yuboriladigan order kartasi matni — role bosqichiga qarab tugmalar farq qiladi."""
    total_fmt = f"{order.total:,}".replace(",", " ")
    return (
        f"🆕 *YANGI BUYURTMA #{order.orderNumber}*\n\n"
        f"👤 Ism: {order.firstName or '—'}\n"
        f"👤 Familiya: {order.lastName or '—'}\n"
        f"📞 Telefon: {order.phone or '—'}\n\n"
        f"{_format_items(order)}\n\n"
        f"💰 *JAMI: {total_fmt} so'm*\n\n"
        f"💳 To'lov: {_payment_label(order.paymentMethod.value if order.paymentMethod else None)}\n"
        f"📍 Location: {_location_line(order)}\n\n"
        f"Holat: *{order.status.value}*"
    )


async def post_order_to_group(order: Order) -> int:
    """Order birinchi marta guruhga yuboriladi (mijoz final tasdiqlagandan keyin)."""
    message = await bot.send_message(
        chat_id=settings.RESTAURANT_GROUP_ID,
        text=_order_card_text(order),
        reply_markup=keyboard_for_status(order.id, order.status),
    )
    return message.message_id


async def update_group_order_card(order: Order) -> None:
    """Status o'zgarganda guruhdagi kartani yangilaydi (tugmalar ham almashadi)."""
    if not order.groupMessageId:
        return
    try:
        await bot.edit_message_text(
            chat_id=settings.RESTAURANT_GROUP_ID,
            message_id=order.groupMessageId,
            text=_order_card_text(order),
            reply_markup=keyboard_for_status(order.id, order.status),
        )
    except TelegramBadRequest:
        # Xabar allaqachon shu matnda bo'lsa Telegram xato qaytaradi — e'tiborsiz qoldiramiz
        pass


CUSTOMER_MESSAGES = {
    "CONFIRMED": "✅ Buyurtmangiz tasdiqlandi!\n\n👨‍🍳 Buyurtma tayyorlanmoqda...",
    "PREPARING": "👨‍🍳 Buyurtmangiz tayyorlanmoqda...",
    "READY": "🍔 Buyurtmangiz tayyor!",
    "DELIVERING": "🛵 Buyurtmangiz yetkazib berilmoqda!",
    "COMPLETED": "✅ Buyurtma bajarildi!",
    "REJECTED": "❌ Afsuski, buyurtmangizni restoran qabul qila olmadi.",
    "CANCELLED": "❌ Buyurtma bekor qilindi.",
}


async def notify_customer_status(order: Order) -> None:
    """Mijozga status haqida DM yuboradi. Guruh haqida hech qanday texnik ma'lumot berilmaydi."""
    text = CUSTOMER_MESSAGES.get(order.status.value)
    if not text:
        return
    try:
        await bot.send_message(chat_id=order.user.telegramId, text=f"*Buyurtma #{order.orderNumber}*\n\n{text}")
    except TelegramForbiddenError:
        # Foydalanuvchi botni bloklagan bo'lishi mumkin — order oqimini to'xtatmaymiz
        pass
