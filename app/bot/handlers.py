from __future__ import annotations
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot.keyboards import panel_keyboard, start_keyboard
from app.database import AsyncSessionLocal
from app.models.enums import StaffRole
from app.models.staff import Staff
from app.services.orders import OrderError, transition_order_status


router = Router()


# ============================================================
# /start
# ============================================================

@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "🍔 *RESTAURANT*ga xush kelibsiz!\n\n"
        "Eng mazali gamburger, shashlik va fastfoodlarni "
        "Telegram orqali buyurtma qiling.\n\n"
        "Kerakli bo‘limni quyidagi menyudan tanlang 👇",
        reply_markup=start_keyboard(),
        parse_mode="Markdown",
    )


# ============================================================
# 📦 BUYURTMALARIM
# ============================================================

@router.message(F.text == "📦 Buyurtmalarim")
async def handle_my_orders(message: Message) -> None:
    """
    Hozircha foydalanuvchiga Mini App orqali buyurtmalarini
    ko‘rish imkonini beradi.

    Keyinchalik bu yerga PostgreSQL'dan real orderlarni
    chiqarish logikasini ulash mumkin.
    """

    await message.answer(
        "📦 *Buyurtmalarim*\n\n"
        "Buyurtmalaringizni ko‘rish uchun "
        "🛒 *Buyurtma berish* tugmasini bosib Mini App'ni oching.\n\n"
        "U yerda buyurtmalaringiz tarixi va holatini ko‘rishingiz mumkin.",
        parse_mode="Markdown",
    )


# ============================================================
# 📍 MANZILIM
# ============================================================

@router.message(F.text == "📍 Manzilim")
async def handle_address(message: Message) -> None:
    await message.answer(
        "📍 *Manzilim*\n\n"
        "Buyurtma berish vaqtida yetkazib berish manzilingizni "
        "Mini App ichida kiritishingiz mumkin.",
        parse_mode="Markdown",
    )


# ============================================================
# ☎️ ALOQA
# ============================================================

@router.message(F.text == "☎️ Aloqa")
async def handle_contact(message: Message) -> None:
    await message.answer(
        "☎️ *RESTAURANT aloqa*\n\n"
        "Buyurtma yoki boshqa savollaringiz bo‘lsa, "
        "restoran administratori bilan bog‘laning.",
        parse_mode="Markdown",
    )


# ============================================================
# ℹ️ BIZ HAQIMIZDA
# ============================================================

@router.message(F.text == "ℹ️ Biz haqimizda")
async def handle_about(message: Message) -> None:
    await message.answer(
        "ℹ️ *RESTAURANT* 🍔\n\n"
        "Biz mazali gamburger, shashlik va fastfoodlarni "
        "tez va qulay tarzda yetkazib beramiz.\n\n"
        "Buyurtmangizni Telegram Mini App orqali "
        "oson berishingiz mumkin.",
        parse_mode="Markdown",
    )


# ============================================================
# /panel
# ============================================================

@router.message(Command("panel"))
async def handle_panel(message: Message) -> None:
    """
    Xodimlar admin panelni /panel orqali ochadi.
    Faqat Staff jadvalida mavjud xodimga ruxsat beriladi.
    """

    if not message.from_user:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Staff).where(
                Staff.telegramId == str(message.from_user.id)
            )
        )

        staff = result.scalar_one_or_none()

    if not staff:
        await message.answer(
            "❌ Siz xodim sifatida ro‘yxatdan o‘tmagansiz."
        )
        return

    if not staff.isActive:
        await message.answer(
            "❌ Sizning xodim hisobingiz faol emas."
        )
        return

    await message.answer(
        "🛠 *RESTAURANT boshqaruv paneli*",
        reply_markup=panel_keyboard(),
        parse_mode="Markdown",
    )


# ============================================================
# ORDER CALLBACK
# ============================================================

@router.callback_query(F.data.startswith("order:"))
async def handle_order_callback(callback: CallbackQuery) -> None:
    """
    Telegram restoran guruhidagi order tugmalari:

    QABUL QILISH
    RAD ETISH
    TAYYORLANMOQDA
    TAYYOR
    YETKAZIB BERILMOQDA
    BAJARILDI
    """

    data = callback.data or ""

    parts = data.split(":")

    if len(parts) != 3:
        await callback.answer(
            "Noto‘g‘ri buyurtma ma'lumoti.",
            show_alert=True,
        )
        return

    _, order_id, action = parts

    if not callback.from_user:
        await callback.answer(
            "Foydalanuvchi aniqlanmadi.",
            show_alert=True,
        )
        return

    telegram_id = str(callback.from_user.id)

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Staff).where(
                Staff.telegramId == telegram_id
            )
        )

        staff = result.scalar_one_or_none()

        if not staff:
            await callback.answer(
                "❌ Siz xodim sifatida ro‘yxatdan o‘tmagansiz.",
                show_alert=True,
            )
            return

        if not staff.isActive:
            await callback.answer(
                "❌ Sizning xodim hisobingiz faol emas.",
                show_alert=True,
            )
            return

        try:
            await transition_order_status(
                db,
                order_id,
                action,
                staff.id,
                StaffRole(staff.role),
            )

            await db.commit()

            await callback.answer(
                "✅ Buyurtma holati yangilandi."
            )

        except OrderError as err:
            await callback.answer(
                err.message,
                show_alert=True,
            )

        except Exception as err:
            await db.rollback()

            print(
                f"Order status error: {err}"
            )

            await callback.answer(
                "❌ Xatolik yuz berdi.",
                show_alert=True,
            )
