"""
Barcha modellarni shu yerda import qilamiz — shunda SQLAlchemy mapper
konfiguratsiyasi (relationship string reference'lari) to'g'ri hal qilinadi
va Alembic autogenerate uchun Base.metadata to'liq bo'ladi.
"""
from app.models.user import User, Address  # noqa: F401
from app.models.staff import Staff  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.banner import Banner  # noqa: F401
from app.models.order import Order, OrderItem, Payment, OrderStatusHistory  # noqa: F401
from app.models.review import Review  # noqa: F401

__all__ = [
    "User",
    "Address",
    "Staff",
    "Category",
    "Product",
    "Banner",
    "Order",
    "OrderItem",
    "Payment",
    "OrderStatusHistory",
    "Review",
]
