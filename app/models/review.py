from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.cuid import cuid


class Review(Base):
    __tablename__ = "Review"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("Order.id"), unique=True, nullable=False)
    userId: Mapped[str] = mapped_column(String, ForeignKey("User.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="review")
    user: Mapped["User"] = relationship(back_populates="reviews")
