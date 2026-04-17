from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from app.core.database import Base
from datetime import datetime

class PlatformHealth(Base):
    """
    Historical record of platform-level scraping health.
    Aggregated from CrawlTasks to allow long-term trend analysis.
    """
    __tablename__ = "platform_health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    
    # Store JSON breakdown of error codes (e.g. {"BLOCKED": 2, "TIMEOUT": 1})
    error_breakdown = Column(JSON, nullable=True)
    
    # Calculated status: healthy, degraded, critical
    status = Column(String(20), default="healthy")

    # Metadata for the batch that generated this snapshot
    task_id = Column(Integer, nullable=True)
