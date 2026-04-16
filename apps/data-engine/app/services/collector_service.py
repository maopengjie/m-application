import random
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import ProductSKU, PriceHistory
from app.models.task import CrawlTask
from app.repositories.product_repository import ProductRepository
from app.services.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.repo = ProductRepository()
        self.base_scraper = BaseScraper()

    def run_collection(self, db: Session):
        """
        Main collection entry point.
        """
        # 1. Concurrency Guard: Ensure only one price_update task runs at a time
        existing_task = (
            db.query(CrawlTask)
            .filter(CrawlTask.task_type == "price_update", CrawlTask.status == "running")
            .first()
        )
        if existing_task:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409, 
                detail=f"Conflict: A price update task (ID: {existing_task.id}) is already active."
            )

        task = CrawlTask(
            task_type="price_update",
            status="running",
            start_time=datetime.now()
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            skus = db.query(ProductSKU).all()
            task.total_count = len(skus)
            
            success_count = 0
            failed_count = 0
            errors = []

            for sku in skus:
                try:
                    # In a real system, we'd have platform-specific URLs in the model
                    # For now, we simulate the "scraping" outcome for different platforms
                    new_price = self._scrape_sku_price(sku)
                    
                    if new_price:
                        # Update current price
                        sku.price = new_price
                        sku.updated_at = datetime.now()
                        
                        # Record in history
                        history = PriceHistory(
                            sku_id=sku.id,
                            price=new_price,
                            recorded_at=datetime.now()
                        )
                        db.add(history)
                        success_count += 1
                    else:
                        raise Exception(f"Failed to fetch price for {sku.platform}")
                        
                except Exception as e:
                    failed_count += 1
                    errors.append(f"SKU {sku.id} ({sku.platform}) error: {str(e)}")

            task.success_count = success_count
            task.failed_count = failed_count
            task.status = "success" if failed_count == 0 else "partial_success"
            
            # Store all errors in metadata for deep auditing
            if not task.metadata_json:
                task.metadata_json = {}
            task.metadata_json["all_errors"] = errors
            
            if errors:
                log_limit = 50
                summary = "\n".join(errors[:log_limit])
                if len(errors) > log_limit:
                    summary += f"\n... and {len(errors) - log_limit} more errors. See metadata_json for full log."
                task.error_log = summary
            
            task.end_time = datetime.now()
            db.commit()
            
            logger.info(f"CollectorService Run: {success_count} success, {failed_count} failed. Task ID: {task.id}")
            return success_count

        except Exception as e:
            task.status = "failed"
            task.error_log = str(e)
            task.end_time = datetime.now()
            db.commit()
            logger.error(f"CollectorService Task {task.id} CRITICAL FAILURE: {e}")
            raise e

    def _scrape_sku_price(self, sku: ProductSKU) -> Optional[float]:
        """
        Fetch price for a given SKU. 
        Currently supports simulated price logic for MVP.
        TODO: Integrate platform-specific scrapers (JDScraper, TmallScraper, etc.)
        """
        # In the future, we will dispatch based on platform:
        # scraper = ScraperFactory.get_scraper(sku.platform)
        # if sku.buy_url:
        #     return scraper.fetch_price(sku.buy_url)
        
        return self._simulate_scrape(sku)

    def _simulate_scrape(self, sku: ProductSKU) -> Optional[float]:
        """
        Placeholder logic to simulate the 'true crawler' experience during MVP.
        Maintains a 95% success rate for error-handling testing.
        """
        # random.uniform(0.1, 0.5) delay is already in BaseScraper.fetch_url 
        # but we call simulate here to avoid hitting real networks in baseline MVP
        if random.random() < 0.05:
            logger.warning(f"Simulated crawl failure for SKU {sku.id} ({sku.platform})")
            return None
            
        old_price = float(sku.price)
        fluctuation = random.uniform(-0.015, 0.015)
        new_price = round(old_price * (1 + fluctuation), 2)
        
        return new_price
