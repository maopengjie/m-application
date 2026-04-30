import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.scraper_alert import ScraperAlert
from app.core.database import SessionLocal

logger = logging.getLogger("Notifier")

class NotifierService:
    """
    Centralized service for dispatching system alerts to various channels.
    Supports Log disclosure, DB persistence, and external Webhooks.
    """
    
    # Example Webhook - should be moved to config in production
    PRICE_INTELLIGENCE_WEBHOOK = None 

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

    @classmethod
    async def send_price_drop_alert(cls, product_name: str, platform: str, old_price: float, new_price: float, buy_url: str):
        """
        [1.1 深度情报] 发送全网最低价变动预警
        """
        drop_percent = round((1 - float(new_price) / float(old_price)) * 100, 1) if old_price > 0 else 0
        content = (
            f"🚀 【价格预警】全网最低价变动！\n"
            f"📦 商品：{product_name}\n"
            f"🏢 平台：{platform}\n"
            f"📉 价格：¥{old_price} -> ¥{new_price} (降幅 {drop_percent}%)\n"
            f"🔗 链接：{buy_url}\n"
            f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        logger.info(f"PRICE_DROP_ALERT: {product_name} at {new_price}")
        
        # Trigger webhook if configured
        if cls.PRICE_INTELLIGENCE_WEBHOOK:
            await cls._trigger_webhook(cls.PRICE_INTELLIGENCE_WEBHOOK, content)

    @classmethod
    async def _trigger_webhook(cls, url: str, content: str):
         try:
             async with httpx.AsyncClient() as client:
                 # Generic markdown format (e.g. for Lark/WeCom)
                 payload = {
                     "msg_type": "interactive",
                     "card": {
                         "header": {"title": {"tag": "plain_text", "content": "情报中心预警"}},
                         "elements": [{"tag": "markdown", "content": content}]
                     }
                 }
                 await client.post(url, json=payload)
         except Exception as e:
             logger.error(f"Webhook delivery failed: {e}")
