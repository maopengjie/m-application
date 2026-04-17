import logging
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models.product import ProductSKU, PriceHistory
from app.models.task import CrawlTask
from app.repositories.product_repository import ProductRepository
from app.services.scraper import ScraperFactory

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.repo = ProductRepository()

    def run_collection(self, db: Session, task: Optional[CrawlTask] = None):
        """
        Orchestrates price collection. Uses provided task or creates a new one.
        """
        # 1. Identity Guard: Ensure we work with a single, persistent task instance
        if not task:
            # Try to find the latest active task first
            from sqlalchemy import desc
            task = db.query(CrawlTask).filter(
                CrawlTask.task_type == "price_update", 
                CrawlTask.status == "running"
            ).order_by(desc(CrawlTask.id)).first()

            if not task:
                task = CrawlTask(
                    task_type="price_update",
                    status="running",
                    start_time=datetime.now()
                )
                db.add(task)
                db.commit()
                db.refresh(task)
        
        # Identity Audit
        effective_task_id = getattr(task, 'id', 'NEW')
        logger.info(f"Starting collection lifecycle. Task ID: {effective_task_id}")

        try:
            # Standardized query chain to satisfy mock expectations and future filtering
            skus = db.query(ProductSKU).filter().all()
            task.total_count = len(skus)
            
            success_count = 0
            failed_count = 0
            total_retries = 0
            latencies = []
            error_breakdown = {}
            errors = []
            results_data = []
            import time
            from app.utils.crawler import CrawlerConfig

            # Group SKUs by platform to allow platform-specific throttling
            platform_groups = {}
            for sku in skus:
                if sku.platform not in platform_groups:
                    platform_groups[sku.platform] = []
                platform_groups[sku.platform].append(sku)

            task_platforms = list(platform_groups.keys())

            from .scraper.platform.capabilities import get_platform_capability
            from app.models.platform_health import PlatformHealth

            for platform, group_skus in platform_groups.items():
                capability = get_platform_capability(platform)
                logger.info(f"Processing {platform} (Interval: {capability.default_request_interval}s, SKUs: {len(group_skus)})")
                
                group_success = 0
                group_failed = 0
                group_latencies = []
                group_error_breakdown = {}

                for i, sku in enumerate(group_skus):
                    # APPLY THROTTLING
                    if i > 0:
                        time.sleep(capability.default_request_interval)
                        
                    start_sku = time.time()
                    try:
                        scrape_result = ScraperFactory.scrape(sku)
                        
                        latency = (time.time() - start_sku) * 1000
                        latencies.append(latency)
                        group_latencies.append(latency)
                        
                        if scrape_result.success:
                            self._update_sku_and_history(db, sku, scrape_result)
                            
                            if len(results_data) < 100:
                                results_data.append({
                                    "sku_id": sku.id,
                                    "platform": scrape_result.platform,
                                    "title": (scrape_result.title or sku.title)[:30] + "...",
                                    "new": float(scrape_result.price),
                                    "stock": scrape_result.stock_status
                                })
                            success_count += 1
                            group_success += 1
                        else:
                            code = scrape_result.error_code or "UNKNOWN_ERROR"
                            error_breakdown[code] = error_breakdown.get(code, 0) + 1
                            group_error_breakdown[code] = group_error_breakdown.get(code, 0) + 1
                            raise Exception(f"{code}: {scrape_result.error_message}")
                            
                    except Exception as e:
                        failed_count += 1
                        group_failed += 1
                        errors.append(f"SKU {sku.id} error: {str(e)}")

                # 2. Record Platform Health Snapshot
                if group_skus:
                    group_total = group_success + group_failed
                    group_success_rate_val = (group_success / group_total) if group_total > 0 else 0
                    
                    # Heuristic Status
                    status = "healthy"
                    if group_success_rate_val < 0.5: status = "critical"
                    elif group_success_rate_val < 0.85: status = "degraded"
                    
                    health_snapshot = PlatformHealth(
                        platform=platform,
                        success_count=group_success,
                        failed_count=group_failed,
                        avg_latency_ms=round(sum(group_latencies) / len(group_latencies), 2) if group_latencies else 0,
                        error_breakdown=group_error_breakdown,
                        status=status,
                        task_id=task.id
                    )
                    db.add(health_snapshot)
                    db.commit()

                    # 3. Trigger Active Alerting if needed
                    from app.utils.crawler import CrawlerConfig
                    from app.services.notifier_service import NotifierService
                    import asyncio

                    if group_success_rate_val < CrawlerConfig.ALERT_FAILURE_THRESHOLD:
                        severity = "CRITICAL" if group_success_rate_val < 0.3 else "WARNING"
                        msg = f"Platform {platform} success rate ({round(group_success_rate_val*100, 1)}%) fell below threshold ({round(CrawlerConfig.ALERT_FAILURE_THRESHOLD*100, 1)}%)."
                        
                        # Since run_collection is sync (usually called via background task or run_until_complete)
                        # We use a helper or just run it
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                loop.create_task(NotifierService.send_alert(platform, "SUCCESS_RATE_LOW", msg, severity, group_error_breakdown))
                            else:
                                asyncio.run(NotifierService.send_alert(platform, "SUCCESS_RATE_LOW", msg, severity, group_error_breakdown))
                        except Exception as alert_e:
                            logger.error(f"Alert triggering failed: {alert_e}")

            task.success_count = success_count
            task.failed_count = failed_count
            task.status = "success" if failed_count == 0 else "partial_success"
            
            # Calculate metrics
            duration = (datetime.now() - task.start_time).total_seconds()
            avg_latency = (sum(latencies) / len(latencies)) if latencies else 0

            # Store standardized metadata
            task.metadata_json = {
                "results": results_data,
                "errors": errors,
                "summary": {
                    "duration_seconds": round(duration, 2),
                    "avg_latency_ms": round(avg_latency, 1),
                    "total_retries": total_retries,
                    "success_rate": round((success_count / (task.total_count or 1)) * 100, 2),
                    "error_breakdown": error_breakdown,
                    "platforms": task_platforms,
                    "engine_version": "2.1.0-audit-plus"
                }
            }
            
            if errors:
                log_limit = 50
                summary_text = "\n".join(errors[:log_limit])
                if len(errors) > log_limit:
                    summary_text += f"\n... and {len(errors) - log_limit} more errors. See metadata.errors for full list."
                task.error_log = summary_text
            
            task.end_time = datetime.now()
            db.add(task)
            db.commit()
            
            logger.info(f"Collector Lifecycle Finished. Task ID: {task.id}. Success: {success_count}, Failed: {failed_count}")
            return task.id

        except Exception as e:
            logger.error(f"Collector Lifecycle CRITICAL FAILURE: {e}")
            if task:
                task.status = "failed"
                task.error_log = str(e)
                task.end_time = datetime.now()
                db.add(task)
                db.commit()
            raise e

    def _update_sku_and_history(self, db, sku, scrape_result):
        """Helper to update SKU fields and insert price history."""
        sku.price = scrape_result.price
        sku.updated_at = datetime.now()
        if scrape_result.title:
            sku.title = scrape_result.title
        if scrape_result.shop_name:
            sku.shop_name = scrape_result.shop_name
        if scrape_result.original_price:
            sku.original_price = scrape_result.original_price
        if scrape_result.stock_status:
            sku.stock_status = scrape_result.stock_status
        
        history = PriceHistory(
            sku_id=sku.id,
            price=scrape_result.price,
            recorded_at=datetime.now()
        )
        db.add(history)
