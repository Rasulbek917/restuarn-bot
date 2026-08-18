"""initial schema (mirrors prisma/schema.prisma)

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-18

MUHIM: Bu migratsiya faqat YANGI (bo'sh) database uchun mo'ljallangan.

Agar sizda allaqachon Prisma orqali migratsiya qilingan Neon database bor bo'lsa,
bu faylni ISHLATMANG — jadvallar allaqachon mavjud. Buning o'rniga:

    alembic stamp head

buyrug'ini ishlating — bu faqat Alembic'ning "hozirgi holat shu revisiyaga mos
keladi" deb belgilashini bildiradi, hech qanday DDL bajarmaydi va mavjud
ma'lumotlarga tegmaydi.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Enum type'larni avval qo'lda yaratamiz, keyin ustunlarda create_type=False
    # bilan ishlatamiz — aks holda SQLAlchemy CREATE TYPE'ni ikki marta chiqarib,
    # "type already exists" xatosiga olib keladi.
    sa.Enum("ADMIN", "COOK", "COURIER", name="StaffRole").create(bind, checkfirst=True)
    sa.Enum(
        "PENDING", "CONFIRMED", "PREPARING", "READY", "DELIVERING", "COMPLETED", "CANCELLED", "REJECTED",
        name="OrderStatus",
    ).create(bind, checkfirst=True)
    sa.Enum("CASH", "CARD", name="PaymentMethod").create(bind, checkfirst=True)
    sa.Enum("NOT_REQUIRED", "PENDING", "PAID", "FAILED", name="PaymentStatus").create(bind, checkfirst=True)

    staff_role = sa.Enum("ADMIN", "COOK", "COURIER", name="StaffRole", create_type=False)
    order_status = sa.Enum(
        "PENDING", "CONFIRMED", "PREPARING", "READY", "DELIVERING", "COMPLETED", "CANCELLED", "REJECTED",
        name="OrderStatus",
        create_type=False,
    )
    payment_method = sa.Enum("CASH", "CARD", name="PaymentMethod", create_type=False)
    payment_status = sa.Enum("NOT_REQUIRED", "PENDING", "PAID", "FAILED", name="PaymentStatus", create_type=False)

    op.create_table(
        "User",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("telegramId", sa.String(), nullable=False, unique=True),
        sa.Column("firstName", sa.String(), nullable=True),
        sa.Column("lastName", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("languageCode", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "Staff",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("telegramId", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", staff_role, nullable=False),
        sa.Column("isActive", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "Category",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("isActive", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "Product",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("categoryId", sa.String(), sa.ForeignKey("Category.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("imageUrl", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("isAvailable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "Banner",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("imageUrl", sa.String(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("isActive", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "Address",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("userId", sa.String(), sa.ForeignKey("User.id"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("rawText", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.execute('CREATE SEQUENCE IF NOT EXISTS "Order_orderNumber_seq"')

    op.create_table(
        "Order",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "orderNumber",
            sa.Integer(),
            nullable=False,
            unique=True,
            server_default=sa.text('nextval(\'"Order_orderNumber_seq"\')'),
        ),
        sa.Column("userId", sa.String(), sa.ForeignKey("User.id"), nullable=False),
        sa.Column("status", order_status, nullable=False, server_default="PENDING"),
        sa.Column("paymentMethod", payment_method, nullable=True),
        sa.Column("paymentStatus", payment_status, nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("addressId", sa.String(), sa.ForeignKey("Address.id"), nullable=True),
        sa.Column("firstName", sa.String(), nullable=True),
        sa.Column("lastName", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("groupMessageId", sa.Integer(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute('ALTER SEQUENCE "Order_orderNumber_seq" OWNED BY "Order"."orderNumber"')

    op.create_table(
        "OrderItem",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("orderId", sa.String(), sa.ForeignKey("Order.id", ondelete="CASCADE"), nullable=False),
        sa.Column("productId", sa.String(), sa.ForeignKey("Product.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
    )

    op.create_table(
        "Payment",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("orderId", sa.String(), sa.ForeignKey("Order.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("providerRef", sa.String(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", payment_status, nullable=False, server_default="PENDING"),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "Review",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("orderId", sa.String(), sa.ForeignKey("Order.id"), nullable=False, unique=True),
        sa.Column("userId", sa.String(), sa.ForeignKey("User.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "OrderStatusHistory",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("orderId", sa.String(), sa.ForeignKey("Order.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("staffId", sa.String(), sa.ForeignKey("Staff.id"), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("OrderStatusHistory")
    op.drop_table("Review")
    op.drop_table("Payment")
    op.drop_table("OrderItem")
    op.drop_table("Order")
    op.execute('DROP SEQUENCE IF EXISTS "Order_orderNumber_seq"')
    op.drop_table("Address")
    op.drop_table("Banner")
    op.drop_table("Product")
    op.drop_table("Category")
    op.drop_table("Staff")
    op.drop_table("User")

    sa.Enum(name="PaymentStatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="PaymentMethod").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="OrderStatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="StaffRole").drop(op.get_bind(), checkfirst=True)
