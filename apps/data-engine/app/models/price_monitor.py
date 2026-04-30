from typing import Optional
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class PriceMonitor(Base, TimestampMixin):
    __tablename__ = "price_monitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    platform: Mapped[str] = mapped_column(String(50))  # e.g., 'amazon', 'jd', 'taobao'
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, paused
