from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import Staff
from app.models.user import User
from app.schemas.auth import (
    CustomerPublic,
    StaffAuthResponse,
    StaffPublic,
    TelegramAuthRequest,
    TelegramAuthResponse,
)
from app.utils.security import sign_customer_token, sign_staff_token, verify_telegram_init_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/telegram", response_model=TelegramAuthResponse)
async def telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """Mini App ochilganda chaqiriladi: initData → validate → user upsert → JWT."""
    result = verify_telegram_init_data(body.initData)
    if not result.ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid Telegram initData: {result.reason}")

    tg_user = result.user
    telegram_id = str(tg_user.id)

    existing = (await db.execute(select(User).where(User.telegramId == telegram_id))).scalar_one_or_none()
    if existing:
        existing.firstName = tg_user.first_name
        existing.lastName = tg_user.last_name
        existing.username = tg_user.username
        existing.languageCode = tg_user.language_code
        user = existing
    else:
        user = User(
            telegramId=telegram_id,
            firstName=tg_user.first_name,
            lastName=tg_user.last_name,
            username=tg_user.username,
            languageCode=tg_user.language_code,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    token = sign_customer_token(user.id, user.telegramId)
    return TelegramAuthResponse(
        token=token, user=CustomerPublic(id=user.id, firstName=user.firstName, lastName=user.lastName)
    )


@router.post("/staff/telegram", response_model=StaffAuthResponse)
async def staff_telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """Admin panel / staff login: bir xil initData mexanizmi, lekin Staff jadvalida
    ro'yxatdan o'tgan bo'lishi shart — shunchaki Telegram akkaunti borligi kifoya emas."""
    result = verify_telegram_init_data(body.initData)
    if not result.ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Telegram initData")

    telegram_id = str(result.user.id)
    staff = (await db.execute(select(Staff).where(Staff.telegramId == telegram_id))).scalar_one_or_none()
    if not staff or not staff.isActive:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Siz xodim sifatida ro'yxatdan o'tmagansiz")

    token = sign_staff_token(staff.id, staff.telegramId, staff.role.value)
    return StaffAuthResponse(token=token, staff=StaffPublic(id=staff.id, name=staff.name, role=staff.role.value))
