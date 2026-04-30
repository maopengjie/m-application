from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.core.database import Base
from datetime import datetime

class ScraperAlert(Base):
    """
    Log of automated alerts triggered by the scraping engine.
    """
    __tablename__ = "scraper_alerts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), index=True)
    alert_type = Column(String(50)) # e.g., SUCCESS_RATE_LOW
    severity = Column(String(20))   # WARNING, CRITICAL
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    is_resolved = Column(Boolean, default=False)
    
    # Context (e.g., Task ID or threshold value)
    metadata_json = Column(Text, nullable=True) 
