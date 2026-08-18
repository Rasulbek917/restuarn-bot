from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: int
    categoryId: str
    imageUrl: Optional[str] = None
    description: Optional[str] = None
    isAvailable: Optional[bool] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    categoryId: Optional[str] = None
    imageUrl: Optional[str] = None
    description: Optional[str] = None
    isAvailable: Optional[bool] = None


class CategoryCreate(BaseModel):
    name: str
    order: Optional[int] = None
    isActive: Optional[bool] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    isActive: Optional[bool] = None


class BannerCreate(BaseModel):
    imageUrl: str
    order: Optional[int] = None
    isActive: Optional[bool] = None


class BannerUpdate(BaseModel):
    imageUrl: Optional[str] = None
    order: Optional[int] = None
    isActive: Optional[bool] = None


class StaffCreate(BaseModel):
    telegramId: str
    name: str
    role: Literal["ADMIN", "COOK", "COURIER"]


class StaffUpdate(BaseModel):
    telegramId: Optional[str] = None
    name: Optional[str] = None
    role: Optional[Literal["ADMIN", "COOK", "COURIER"]] = None
    isActive: Optional[bool] = None


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    telegramId: str
    name: str
    role: str
    isActive: bool
    createdAt: datetime


class DashboardOut(BaseModel):
    todayOrdersCount: int
    todaySales: int
    activeOrders: int
    completedToday: int
    cancelledToday: int
    averageRating: float
