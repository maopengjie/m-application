from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.decision import DecisionResponse
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])
decision_service = DecisionService()


@router.get("/{sku_id}", response_model=DecisionResponse)
def get_decision(
    sku_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """Get the AI shopping decision for a specific SKU."""
    decision = decision_service.get_decision(db, sku_id)
    if not decision:
        raise HTTPException(status_code=404, detail="SKU not found")
    return decision
