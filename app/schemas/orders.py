from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItemIn(BaseModel):
    productId: str
    quantity: int = Field(ge=1, le=50)


class CreateOrderRequest(BaseModel):
    items: List[OrderItemIn] = Field(min_length=1)


class PaymentMethodRequest(BaseModel):
    method: Literal["CASH", "CARD"]


class AddressRequest(BaseModel):
    latitude: float
    longitude: float
    rawText: Optional[str] = None


class ContactRequest(BaseModel):
    phone: str = Field(min_length=5)
    firstName: str = Field(min_length=1)
    lastName: str = Field(min_length=1)


class ReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    orderId: str
    productId: str
    name: str
    price: int
    quantity: int


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    userId: str
    latitude: float
    longitude: float
    rawText: Optional[str] = None
    createdAt: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    orderNumber: int
    userId: str
    status: str
    paymentMethod: Optional[str] = None
    paymentStatus: str
    total: int
    addressId: Optional[str] = None
    address: Optional[AddressOut] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    groupMessageId: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime
    items: List[OrderItemOut] = []


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    orderId: str
    userId: str
    rating: int
    comment: Optional[str] = None
    createdAt: datetime
