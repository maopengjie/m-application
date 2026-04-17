import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.scraper.factory import ScraperFactory
from app.models.platform_health import PlatformHealth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SmokeSuite")

# FIXED SAMPLE POOL
SMOKE_SAMPLES = [
    {"platform": "JD", "sku_id": "100067644265", "buy_url": "https://item.jd.com/100067644265.html"},
    {"platform": "Tmall", "sku_id": "654321", "buy_url": "https://detail.tmall.com/item.htm?id=654321"},
    {"platform": "PDD", "sku_id": "998877", "buy_url": "https://mobile.yangkeduo.com/goods.html?goods_id=998877"}
]

class MockSKU:
    def __init__(self, platform, sku_id, buy_url):
        self.platform = platform
        self.platform_sku_id = sku_id
        self.buy_url = buy_url
        self.title = f"Smoke Test {platform}"

async def run_smoke_test():
    """
    Executes a real-world probe for each platform and records health snapshots.
    """
    logger.info("🚀 Starting Platform Smoke Test Suite...")
    db = SessionLocal()
    
    try:
        for sample in SMOKE_SAMPLES:
            platform = sample["platform"]
            logger.info(f"Probing {platform}...")
            
            sku = MockSKU(platform, sample["sku_id"], sample["buy_url"])
            start_time = datetime.now()
            
            try:
                # Real scrape attempt
                result = await ScraperFactory.scrape_async(sku)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                # Determine status
                status = "healthy" if result.success else "degraded"
                if result.error_code == "BLOCKED": status = "critical"
                
                # Record to PlatformHealth table
                health = PlatformHealth(
                    platform=platform,
                    success_count=1 if result.success else 0,
                    failed_count=0 if result.success else 1,
                    avg_latency_ms=duration,
                    error_breakdown={result.error_code: 1} if not result.success else {},
                    status=status
                )
                db.add(health)
                logger.info(f"Result for {platform}: {'PASS' if result.success else 'FAIL'} ({result.error_code})")
                
            except Exception as e:
                logger.error(f"Critical error probing {platform}: {e}")
                health = PlatformHealth(
                    platform=platform,
                    success_count=0,
                    failed_count=1,
                    status="critical",
                    error_breakdown={"CRASH": 1}
                )
                db.add(health)

        db.commit()
        logger.info("✅ Smoke Test Suite completed and results persisted.")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
