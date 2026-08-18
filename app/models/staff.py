from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StaffRole
from app.utils.cuid import cuid


class Staff(Base):
    __tablename__ = "Staff"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    telegramId: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[StaffRole] = mapped_column(
        Enum(StaffRole, name="StaffRole", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    isActive: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    statusChanges: Mapped[List["OrderStatusHistory"]] = relationship(back_populates="staff")
