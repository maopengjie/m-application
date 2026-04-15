from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PriceMonitorBase(BaseModel):
    name: str
    url: str
    target_price: Optional[float] = None
    platform: str


class PriceMonitorCreate(PriceMonitorBase):
    pass


class PriceMonitorUpdate(BaseModel):
    name: Optional[str] = None
    target_price: Optional[float] = None
    status: Optional[str] = None


class PriceMonitorInDBBase(PriceMonitorBase):
    id: int
    current_price: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceMonitor(PriceMonitorInDBBase):
    pass
