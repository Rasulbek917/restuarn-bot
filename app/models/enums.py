"""
prisma/schema.prisma dagi enumlar bilan bit-baravar (nom va qiymatlar mos kelishi
shart, chunki mavjud Neon database'da shu Postgres enum type'lar allaqachon bor).
"""
import enum


class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    COOK = "COOK"
    COURIER = "COURIER"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"


class PaymentStatus(str, enum.Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
