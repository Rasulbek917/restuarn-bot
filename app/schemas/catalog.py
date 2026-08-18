from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    order: int
    isActive: bool


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    categoryId: str
    name: str
    price: int
    imageUrl: str | None = None
    description: str | None = None
    isAvailable: bool
    createdAt: datetime
    updatedAt: datetime


class BannerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    imageUrl: str
    order: int
    isActive: bool
