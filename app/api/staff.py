from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.enums import StaffRole
from app.models.order import Order
from app.schemas.orders import OrderOut
from app.services.orders import OrderError, transition_order_status
from app.utils.deps import StaffContext, require_staff_auth

router = APIRouter(prefix="/api/staff", tags=["staff"])

STATUS_BY_ROLE = {
    "ADMIN": ["PENDING", "CONFIRMED", "PREPARING", "READY", "DELIVERING"],
    "COOK": ["CONFIRMED", "PREPARING"],
    "COURIER": ["READY", "DELIVERING"],
}

ACTIONS = ["accept", "reject", "preparing", "ready", "delivering", "complete"]


@router.get("/orders", response_model=list[OrderOut])
async def staff_orders(staff: StaffContext = Depends(require_staff_auth), db: AsyncSession = Depends(get_db)):
    """Staffning roliga tegishli aktiv orderlar ro'yxati."""
    statuses = STATUS_BY_ROLE.get(staff.role, [])
    result = await db.execute(
        select(Order)
        .where(Order.status.in_(statuses))
        .options(selectinload(Order.items), selectinload(Order.address))
        .order_by(Order.createdAt.asc())
    )
    return result.scalars().all()


@router.post("/orders/{order_id}/{action}", response_model=OrderOut)
async def staff_order_action(
    order_id: str,
    action: str,
    staff: StaffContext = Depends(require_staff_auth),
    db: AsyncSession = Depends(get_db),
):
    if action not in ACTIONS:
        raise HTTPException(400, "Noma'lum amal")

    try:
        return await transition_order_status(db, order_id, action, staff.staff_id, StaffRole(staff.role))
    except OrderError as err:
        raise HTTPException(status_code=err.status, detail=err.message)
