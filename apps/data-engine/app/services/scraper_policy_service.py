import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.platform_health import PlatformHealth

logger = logging.getLogger(__name__)

class ScraperPolicyService:
    """
    Adaptive Scraping Policy Service.
    Adjusts request intervals based on historical success rates.
    """

    @staticmethod
    def get_adaptive_interval(db: Session, platform: str, base_interval: float) -> float:
        """
        Calculates an adaptive interval based on the last 10 snapshots.
        If success rate is low, it increases the interval (back-off).
        """
        latest_snapshots = (
            db.query(PlatformHealth)
            .filter(PlatformHealth.platform == platform)
            .order_by(desc(PlatformHealth.timestamp))
            .limit(10)
            .all()
        )

        if not latest_snapshots:
            return base_interval

        total_success = sum(s.success_count for s in latest_snapshots)
        total_failed = sum(s.failed_count for s in latest_snapshots)
        total_attempts = total_success + total_failed

        if total_attempts == 0:
            return base_interval

        success_rate = total_success / total_attempts

        # Policy Logic:
        # > 90% success: base_interval
        # 70% - 90% success: 1.5x base_interval
        # 50% - 70% success: 3x base_interval
        # < 50% success: 10x base_interval (Critical back-off)
        
        if success_rate > 0.9:
            multiplier = 1.0
        elif success_rate > 0.7:
            multiplier = 1.5
        elif success_rate > 0.5:
            multiplier = 3.0
        else:
            multiplier = 10.0
            logger.warning(f"Platform {platform} is unstable (success rate {round(success_rate*100, 1)}%). Applying 10x back-off.")

        return base_interval * multiplier
