from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.repositories.analytics_repository import AnalyticsRepository
from app.api.v1.deps import get_current_user, PermissionChecker
from app.utils.responses import response_success

router = APIRouter(prefix="/analytics", tags=["analytics"])
repo = AnalyticsRepository()

class EventCreate(BaseModel):
    event_name: str
    properties: Dict[str, Any] = {}

@router.post("/events")
def log_event(
    *,
    db: Session = Depends(get_db),
    event_in: EventCreate,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Log a tracking event."""
    repo.log_event(db, event_in.event_name, current_user["id"], event_in.properties)
    return response_success(None, "Event logged")

@router.get("/dashboard")
def get_dashboard(
    *,
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    # Only admins can view the dashboard
    _ = Depends(PermissionChecker(["AC_100010"]))
) -> Any:
    """Get aggregated analytics for the dashboard."""
    stats = repo.get_summary_stats(db, days)
    return response_success(stats)
