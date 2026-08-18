"""
FastAPI dependency'lari — TypeScript versiyasidagi middleware/auth.ts o'rniga.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError

from app.utils.security import verify_customer_token, verify_staff_token


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    return authorization[len("Bearer "):]


async def require_customer_auth(authorization: Optional[str] = Header(default=None)) -> str:
    """Mijoz (Mini App) uchun: Authorization: Bearer <jwt>. userId qaytaradi."""
    token = _extract_bearer(authorization)
    try:
        payload = verify_customer_token(token)
        return payload["userId"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@dataclass
class StaffContext:
    staff_id: str
    telegram_id: str
    role: str


async def require_staff_auth(authorization: Optional[str] = Header(default=None)) -> StaffContext:
    """Staff/Admin panel uchun."""
    token = _extract_bearer(authorization)
    try:
        payload = verify_staff_token(token)
        return StaffContext(staff_id=payload["staffId"], telegram_id=payload["telegramId"], role=payload["role"])
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def require_role(*roles: str):
    """Faqat berilgan role(lar)ga ruxsat."""

    async def _checker(staff: StaffContext = Depends(require_staff_auth)) -> StaffContext:
        if staff.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: insufficient role")
        return staff

    return _checker
