from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class CrawlerStartPayload(BaseModel):
    target_url: str


class CrawlPreviewPayload(BaseModel):
    target_url: str
    selector: str | None = None
    dynamic: bool = False


class CrawlTaskResponse(BaseModel):
    id: int
    task_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_count: int
    success_count: int
    failed_count: int
    error_log: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
