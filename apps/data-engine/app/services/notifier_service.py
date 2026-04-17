import logging
import httpx
from typing import Dict, Any
from app.models.scraper_alert import ScraperAlert
from app.core.database import SessionLocal

logger = logging.getLogger("Notifier")

class NotifierService:
    """
    Centralized service for dispatching system alerts to various channels.
    Supports Log disclosure, DB persistence, and external Webhooks.
    """
    
    @classmethod
    async def send_alert(cls, platform: str, alert_type: str, message: str, severity: str = "WARNING", metadata: Dict = None):
        # 1. Log consistently
        log_msg = f"[{severity}] PLATFORM: {platform} | TYPE: {alert_type} | MSG: {message}"
        if severity == "CRITICAL":
            logger.error(log_msg)
        else:
            logger.warning(log_msg)

        # 2. Persist to DB for auditing
        try:
            db = SessionLocal()
            alert = ScraperAlert(
                platform=platform,
                alert_type=alert_type,
                severity=severity,
                message=message,
                metadata_json=str(metadata) if metadata else None
            )
            db.add(alert)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to persist alert to DB: {e}")

        # 3. Optional: Webhook (Placeholder for WeCom/DingTalk)
        # WEBHOOK_URL = "https://example.com/webhook"
        # await cls._trigger_webhook(WEBHOOK_URL, log_msg)

    @classmethod
    async def _trigger_webhook(cls, url: str, content: str):
         try:
             async with httpx.AsyncClient() as client:
                 await client.post(url, json={"msgtype": "text", "text": {"content": content}})
         except Exception as e:
             logger.error(f"Webhook delivery failed: {e}")
