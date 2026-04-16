from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.alert import PriceAlertCreate, PriceAlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])
alert_service = AlertService()


@router.get("", response_model=list[PriceAlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    user_id: int = Query(1),
) -> Any:
    """List price alerts for a user."""
    return alert_service.list_alerts(db, user_id)


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    *,
    db: Session = Depends(get_db),
    alert_in: PriceAlertCreate,
) -> Any:
    """Create a new price alert."""
    return alert_service.create_alert(db, alert_in.model_dump())


@router.delete("/{alert_id}")
def delete_alert(
    *,
    db: Session = Depends(get_db),
    alert_id: int,
) -> Any:
    """Delete a price alert."""
    success = alert_service.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}
