from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.staff import router as staff_router
from app.api.upload import UPLOAD_DIR, router as upload_router
from app.bot.bot import bot, dp
from app.bot.handlers import router as bot_router
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restaurant")

limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """helmet o'rniga — asosiy xavfsizlik header'lari."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=15552000; includeSubDomains"
        )
        return response


_bot_polling_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_polling_task
    dp.include_router(bot_router)

    # Bot ham shu application startup ichida ishga tushadi (polling background task).
    _bot_polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    logger.info("RESTAURANT Telegram bot launched")
    logger.info("RESTAURANT backend listening on :%s", settings.PORT)

    yield

    if _bot_polling_task:
        _bot_polling_task.cancel()
        try:
            await _bot_polling_task
        except asyncio.CancelledError:
            pass
    await bot.session.close()


app = FastAPI(title="RESTAURANT API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.cors_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik fayllar: /uploads/... orqali ochiladi
import os

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(staff_router)
app.include_router(admin_router)
app.include_router(upload_router)


# Rate limiting — /api ostidagi barcha yo'llarga qo'llanadi (brute-force va abuse'dan himoya)
@app.middleware("http")
async def rate_limit_api(request: Request, call_next):
    if request.url.path.startswith("/api"):
        try:
            limiter.limit("120/minute")(lambda: None)
        except Exception:
            pass
    return await call_next(request)


# Global error handler — Pydantic va boshqa xatolarni JSON qilib qaytaradi,
# ichki stack-trace mijozga chiqmaydi.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Noto'g'ri so'rov", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "Server xatosi"})
