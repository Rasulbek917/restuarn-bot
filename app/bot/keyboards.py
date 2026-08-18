from __future__ import annotations

from typing import Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import settings
from app.models.enums import OrderStatus


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🛒 Buyurtma berish",
                    web_app=WebAppInfo(url=settings.MINI_APP_URL),
                )
            ],
            [
                KeyboardButton(text="📦 Buyurtmalarim"),
                KeyboardButton(text="📍 Manzilim"),
            ],
            [
                KeyboardButton(text="☎️ Aloqa"),
                KeyboardButton(text="ℹ️ Biz haqimizda"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Panelni ochish",
                    web_app=WebAppInfo(url=settings.ADMIN_PANEL_URL),
                )
            ]
        ]
    )


def keyboard_for_status(
    order_id: str,
    status: OrderStatus,
) -> Optional[InlineKeyboardMarkup]:

    if status == OrderStatus.CONFIRMED:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👨‍🍳 TAYYORLANMOQDA",
                        callback_data=f"order:{order_id}:preparing",
                    )
                ]
            ]
        )

    if status == OrderStatus.PREPARING:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🍔 TAYYOR",
                        callback_data=f"order:{order_id}:ready",
                    )
                ]
            ]
        )

    if status == OrderStatus.READY:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛵 YETKAZIB BERILMOQDA",
                        callback_data=f"order:{order_id}:delivering",
                    )
                ]
            ]
        )

    if status == OrderStatus.DELIVERING:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ BAJARILDI",
                        callback_data=f"order:{order_id}:complete",
                    )
                ]
            ]
        )

    if status == OrderStatus.PENDING:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ QABUL QILISH",
                        callback_data=f"order:{order_id}:accept",
                    ),
                    InlineKeyboardButton(
                        text="❌ RAD ETISH",
                        callback_data=f"order:{order_id}:reject",
                    ),
                ]
            ]
        )

    return None