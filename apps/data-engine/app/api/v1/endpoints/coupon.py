from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Coupon
from app.schemas.product import Coupon as CouponSchema
from app.utils.responses import response_success
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/coupons", tags=["coupons"], dependencies=[Depends(get_current_user)])

@router.get("")
async def list_coupons(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List all available coupons."""
    coupons = db.query(Coupon).offset(skip).limit(limit).all()
    # Convert SQLAlchemy models to Pydantic schemas for JSON serialization
    data = [CouponSchema.model_validate(c).model_dump() for c in coupons]
    return response_success(data)
