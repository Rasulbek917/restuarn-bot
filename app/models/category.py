from __future__ import annotations

from typing import List

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.cuid import cuid


class Category(Base):
    __tablename__ = "Category"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    products: Mapped[List["Product"]] = relationship(back_populates="category")
