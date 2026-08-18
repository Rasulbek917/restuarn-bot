"""
SQLAlchemy 2.x async engine + session.
"""
from __future__ import annotations

from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _to_asyncpg_url(url: str) -> str:
    """PostgreSQL URL'ni asyncpg uchun moslashtiradi."""
    if url.startswith("postgresql+asyncpg://"):
        return url

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def _clean_database_url(url: str) -> str:
    """
    asyncpg tushunmaydigan sslmode/channel_binding parametrlarini
    URL'dan olib tashlaymiz.
    """
    parts = urlsplit(url)

    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.pop("sslmode", None)
    query.pop("channel_binding", None)

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )


DATABASE_URL = _clean_database_url(
    _to_asyncpg_url(settings.DATABASE_URL)
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={
        "ssl": "require",
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session