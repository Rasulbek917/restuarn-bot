from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.cuid import cuid


class Product(Base):
    __tablename__ = "Product"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    categoryId: Mapped[str] = mapped_column(String, ForeignKey("Category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # so'mda, butun son
    imageUrl: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    isAvailable: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    orderItems: Mapped[List["OrderItem"]] = relationship(back_populates="product")
