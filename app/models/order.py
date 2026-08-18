from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Sequence, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import OrderStatus, PaymentMethod, PaymentStatus, StaffRole
from app.utils.cuid import cuid

# Prisma `@default(autoincrement())` uchun avtomatik yaratgan sequence nomi bilan
# bir xil — shu bilan mavjud Neon database'dagi sequence'ga ulanadi (talab #31).
order_number_seq = Sequence("Order_orderNumber_seq")


class Order(Base):
    __tablename__ = "Order"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    orderNumber: Mapped[int] = mapped_column(
        Integer, order_number_seq, server_default=order_number_seq.next_value(), unique=True, nullable=False
    )
    userId: Mapped[str] = mapped_column(String, ForeignKey("User.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="OrderStatus", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    paymentMethod: Mapped[Optional[PaymentMethod]] = mapped_column(
        Enum(PaymentMethod, name="PaymentMethod", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    paymentStatus: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="PaymentStatus", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        default=PaymentStatus.NOT_REQUIRED,
        server_default=PaymentStatus.NOT_REQUIRED.value,
    )
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    addressId: Mapped[Optional[str]] = mapped_column(String, ForeignKey("Address.id"), nullable=True)
    firstName: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lastName: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    groupMessageId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    address: Mapped[Optional["Address"]] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order")
    review: Mapped[Optional["Review"]] = relationship(back_populates="order")
    statusHistory: Mapped[List["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "OrderItem"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("Order.id", ondelete="CASCADE"), nullable=False)
    productId: Mapped[str] = mapped_column(String, ForeignKey("Product.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)  # order paytidagi nom (frozen snapshot)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # order paytidagi narx (frozen snapshot)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="orderItems")


class Payment(Base):
    __tablename__ = "Payment"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("Order.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # "click" | "payme" | ...
    providerRef: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="PaymentStatus", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="payments")


class OrderStatusHistory(Base):
    __tablename__ = "OrderStatusHistory"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("Order.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="OrderStatus", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    staffId: Mapped[Optional[str]] = mapped_column(String, ForeignKey("Staff.id"), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="statusHistory")
    staff: Mapped[Optional["Staff"]] = relationship(back_populates="statusChanges")
