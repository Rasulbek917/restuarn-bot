"""
Konfiguratsiya — barcha environment variable'lar shu yerda o'qiladi.
TypeScript versiyasidagi backend/src/lib/env.ts bilan bir xil talablar:
majburiy o'zgaruvchi yo'q bo'lsa, ilova ishga tushishda darhol xato beradi.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    NODE_ENV: str = "development"
    PORT: int = 4000

    DATABASE_URL: str

    BOT_TOKEN: str
    RESTAURANT_GROUP_ID: str

    JWT_SECRET: str
    JWT_STAFF_SECRET: str
    JWT_ADMIN_SECRET: str

    MINI_APP_URL: str
    ADMIN_PANEL_URL: str = ""

    PAYMENT_PROVIDER: str = "click"
    PAYMENT_MERCHANT_ID: str = ""
    PAYMENT_SECRET_KEY: str = ""
    PAYMENT_WEBHOOK_SECRET: str = ""

    CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    # required() xatti-harakati: agar majburiy maydon yo'q bo'lsa, pydantic-settings
    # ValidationError beradi — bu Node.js versiyasidagi darhol crash bilan bir xil.
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
