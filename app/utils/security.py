"""
JWT (customer/staff/admin) va Telegram Mini App initData validatsiyasi.
TypeScript versiyasidagi lib/jwt.ts + lib/telegramAuth.ts o'rniga.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional
from urllib.parse import parse_qsl

from jose import JWTError, jwt

from app.config import settings

CUSTOMER_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 kun
STAFF_TOKEN_TTL_SECONDS = 12 * 60 * 60  # 12 soat
INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 soat — replay himoyasi

JWT_ALGORITHM = "HS256"

StaffRoleLiteral = Literal["ADMIN", "COOK", "COURIER"]


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def sign_customer_token(user_id: str, telegram_id: str) -> str:
    payload = {
        "userId": user_id,
        "telegramId": telegram_id,
        "exp": int(time.time()) + CUSTOMER_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_customer_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])


def sign_staff_token(staff_id: str, telegram_id: str, role: StaffRoleLiteral) -> str:
    secret = settings.JWT_ADMIN_SECRET if role == "ADMIN" else settings.JWT_STAFF_SECRET
    payload = {
        "staffId": staff_id,
        "telegramId": telegram_id,
        "role": role,
        "exp": int(time.time()) + STAFF_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def verify_staff_token(token: str) -> dict:
    # ADMIN va STAFF secretlari boshqa-boshqa — avval biri, keyin ikkinchisi bilan sinaymiz
    try:
        return jwt.decode(token, settings.JWT_ADMIN_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return jwt.decode(token, settings.JWT_STAFF_SECRET, algorithms=[JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# Telegram Mini App initData validation
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ---------------------------------------------------------------------------
@dataclass
class TelegramWebAppUser:
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


@dataclass
class InitDataResult:
    ok: bool
    user: Optional[TelegramWebAppUser] = None
    reason: Optional[str] = None


def verify_telegram_init_data(init_data: str) -> InitDataResult:
    """
    Bu tekshiruvsiz frontenddan kelgan `user` obyektiga ASLO ishonib bo'lmaydi —
    har kim o'zini istalgan telegramId sifatida ko'rsatib yuborishi mumkin edi.
    """
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True)
        params: dict[str, str] = dict(pairs)

        received_hash = params.pop("hash", None)
        if not received_hash:
            return InitDataResult(ok=False, reason="hash missing")

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return InitDataResult(ok=False, reason="hash mismatch")

        auth_date = int(params.get("auth_date", "0") or "0")
        age_seconds = time.time() - auth_date
        if age_seconds > INIT_DATA_MAX_AGE_SECONDS:
            return InitDataResult(ok=False, reason="initData expired")

        user_raw = params.get("user")
        if not user_raw:
            return InitDataResult(ok=False, reason="user missing")

        user_json: dict[str, Any] = json.loads(user_raw)
        user = TelegramWebAppUser(
            id=user_json["id"],
            first_name=user_json.get("first_name", ""),
            last_name=user_json.get("last_name"),
            username=user_json.get("username"),
            language_code=user_json.get("language_code"),
        )
        return InitDataResult(ok=True, user=user)
    except Exception:
        return InitDataResult(ok=False, reason="parse error")
