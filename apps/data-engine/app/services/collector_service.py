import logging
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models.product import ProductSKU, PriceHistory, StockHistory, Product
from app.models.task import CrawlTask
from app.repositories.product_repository import ProductRepository
from app.services.scraper import ScraperFactory
from app.services.scraper_policy_service import ScraperPolicyService
from app.models.platform_health import PlatformHealth
from app.services.notifier_service import NotifierService

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.repo = ProductRepository()

    def run_collection(self, db: Session, task: Optional[CrawlTask] = None):
        """Orchestrates price collection."""
        if not task:
            from sqlalchemy import desc
            task = db.query(CrawlTask).filter(
                CrawlTask.task_type == "price_update", 
                CrawlTask.status == "running"
            ).order_by(desc(CrawlTask.id)).first()

            if not task:
                task = CrawlTask(task_type="price_update", status="running", start_time=datetime.now())
                db.add(task)
                db.commit()
                db.refresh(task)
        
        logger.info(f"Starting collection lifecycle. Task ID: {task.id}")

        try:
            skus = db.query(ProductSKU).filter().all()
            task.total_count = len(skus)
            
            success_count = 0
            failed_count = 0
            latencies = []
            error_breakdown = {}
            errors = []

            platform_groups = {}
            for sku in skus:
                if sku.platform not in platform_groups:
                    platform_groups[sku.platform] = []
                platform_groups[sku.platform].append(sku)

            from .scraper.platform.capabilities import get_platform_capability

            for platform, group_skus in platform_groups.items():
                capability = get_platform_capability(platform)
                adaptive_interval = ScraperPolicyService.get_adaptive_interval(db, platform, capability.default_request_interval)
                
                logger.info(f"Processing {platform} (Adaptive Interval: {adaptive_interval}s, SKUs: {len(group_skus)})")
                
                group_success = 0
                group_failed = 0
                group_latencies = []
                group_error_breakdown = {}

                for i, sku in enumerate(group_skus):
                    if i > 0: time.sleep(adaptive_interval)
                    start_sku = time.time()
                    try:
                        scrape_result = ScraperFactory.scrape(sku)
                        latency = (time.time() - start_sku) * 1000
                        latencies.append(latency)
                        group_latencies.append(latency)
                        
                        if scrape_result.success:
                            # Trigger update and potential alerts
                            self._update_sku_and_history(db, sku, scrape_result)
                            success_count += 1
                            group_success += 1
                        else:
                            code = scrape_result.error_code or "UNKNOWN_ERROR"
                            group_error_breakdown[code] = group_error_breakdown.get(code, 0) + 1
                            raise Exception(f"{code}: {scrape_result.error_message}")
                            
                    except Exception as e:
                        failed_count += 1
                        group_failed += 1
                        errors.append(f"SKU {sku.id} error: {str(e)}")

                if group_skus:
                    group_total = group_success + group_failed
                    group_success_rate = (group_success / group_total) if group_total > 0 else 0
                    status = "healthy"
                    if group_success_rate < 0.5: status = "critical"
                    elif group_success_rate < 0.85: status = "degraded"
                    
                    health_snapshot = PlatformHealth(
                        platform=platform,
                        success_count=group_success,
                        failed_count=group_failed,
                        avg_latency_ms=round(sum(group_latencies) / len(group_latencies), 2) if group_latencies else 0,
                        error_breakdown=group_error_breakdown,
                        status=status,
                        current_interval=adaptive_interval,
                        task_id=task.id
                    )
                    db.add(health_snapshot)
                    db.commit()

            task.success_count = success_count
            task.failed_count = failed_count
            task.status = "success" if failed_count == 0 else "partial_success"
            task.end_time = datetime.now()
            db.add(task)
            db.commit()
            return task.id

        except Exception as e:
            logger.error(f"Collector FAILURE: {e}")
            if task:
                task.status = "failed"
                task.end_time = datetime.now()
                db.add(task)
                db.commit()
            raise e

    def _update_sku_and_history(self, db, sku, scrape_result):
        """Helper to update SKU fields and insert price/stock history."""
        old_price = float(sku.price)
        new_price = float(scrape_result.price)

        # [1.1 深度情报] 实时价格监测预警
        if new_price < old_price:
            logger.info(f"Price drop detected for SKU {sku.id}: {old_price} -> {new_price}")
            product = db.query(Product).filter(Product.id == sku.product_id).first()
            
            # Fire alert async
            try:
                loop = asyncio.get_event_loop()
                coro = NotifierService.send_price_drop_alert(
                    product_name=product.name if product else sku.title,
                    platform=sku.platform,
                    old_price=old_price,
                    new_price=new_price,
                    buy_url=sku.buy_url
                )
                if loop.is_running():
                    loop.create_task(coro)
                else:
                    asyncio.run(coro)
            except Exception as e:
                logger.error(f"Failed to trigger price alert: {e}")

        # Update SKU
        sku.price = scrape_result.price
        sku.updated_at = datetime.now()
        if scrape_result.title: sku.title = scrape_result.title
        if scrape_result.stock_status: sku.stock_status = scrape_result.stock_status
        if scrape_result.visual_hash: sku.visual_hash = scrape_result.visual_hash
        if scrape_result.screenshot_url: sku.last_screenshot = scrape_result.screenshot_url
            
        db.add(PriceHistory(sku_id=sku.id, price=scrape_result.price, recorded_at=datetime.now()))
        db.add(StockHistory(
            sku_id=sku.id, 
            stock_level=scrape_result.stock_level or 0, 
            status=scrape_result.stock_status or "unknown",
            recorded_at=datetime.now()
        ))
