from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    initData: str = Field(min_length=1)


class CustomerPublic(BaseModel):
    id: str
    firstName: str | None = None
    lastName: str | None = None


class TelegramAuthResponse(BaseModel):
    token: str
    user: CustomerPublic


class StaffPublic(BaseModel):
    id: str
    name: str
    role: str


class StaffAuthResponse(BaseModel):
    token: str
    staff: StaffPublic
