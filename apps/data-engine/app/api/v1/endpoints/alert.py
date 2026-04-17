from typing import Any
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.alert import PriceAlertCreate, PriceAlertResponse
from app.services.alert_service import AlertService
from app.api.v1.deps import get_current_user, PermissionChecker

from app.utils.responses import response_success

router = APIRouter(prefix="/alerts", tags=["alerts"])
alert_service = AlertService()


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """List price alerts for a user."""
    alerts = alert_service.list_alerts(db, current_user["id"])
    data = [PriceAlertResponse.model_validate(a) for a in alerts]
    return response_success(data)


@router.post("/scan", dependencies=[Depends(PermissionChecker(["AC_100010"]))])
def scan_alerts(
    db: Session = Depends(get_db),
) -> Any:
    """Manually trigger a scan of all active alerts."""
    triggered = alert_service.check_alerts(db)
    return response_success({"triggered_count": len(triggered)}, "Scan completed")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(
    *,
    db: Session = Depends(get_db),
    alert_in: PriceAlertCreate,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Create a new price alert."""
    payload = alert_in.model_dump()
    payload["user_id"] = current_user["id"] # Enforce setting alert to current user
    alert = alert_service.create_alert(db, payload)
    return response_success(PriceAlertResponse.model_validate(alert))


@router.delete("/{alert_id}")
def delete_alert(
    *,
    db: Session = Depends(get_db),
    alert_id: int,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Delete a price alert."""
    success = alert_service.delete_alert(db, alert_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or unauthorized")
    return response_success(None, "Alert deleted successfully")
